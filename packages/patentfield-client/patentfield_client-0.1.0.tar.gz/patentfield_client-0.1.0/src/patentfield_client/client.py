import io
import os
import time
from typing import Any, Sequence

import httpx
from PIL import Image, UnidentifiedImageError


class PatentfieldAPIError(Exception):
    """Patentfield API 呼び出し時の例外"""
    pass


def _should_retry(status_code: int) -> bool:
    return status_code in (429, 500, 502, 503, 504)


class PatentfieldClient:
    """
    Patentfield API 同期クライアント（httpx.Client ベース）

    認証:
        Authorization: Token <API_TOKEN>
    ベースURL:
        https://api.patentfield.com/api/v1
    """
    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = "https://api.patentfield.com/api/v1",
        timeout: float = 30.0,
        retries: int = 2,
        backoff: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.backoff = backoff
        token = token or os.getenv("PATENTFIELD_API_KEY")
        if not token:
            raise ValueError("PATENTFIELD_API_KEY が設定されていません。")
        headers = {
            "Authorization": f"Token {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "PatentfieldHttpxClient/0.1 (+httpx)",
        }
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers,
        )

    # --- context manager / lifecycle ---
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PatentfieldClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # --- internal helpers ---
    def _handle_error(self, resp: httpx.Response) -> None:
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise PatentfieldAPIError(
                f"{e.request.method} {e.request.url} -> {resp.status_code}: {detail}"
            ) from e

    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        attempt = 0
        while True:
            try:
                resp = self._client.request(method, url, **kwargs)
            except httpx.RequestError as e:
                # 接続系エラーもリトライ対象
                if attempt >= self.retries:
                    raise PatentfieldAPIError(f"Network error: {e}") from e
                time.sleep(self.backoff * (2 ** attempt))
                attempt += 1
                continue

            if _should_retry(resp.status_code) and attempt < self.retries:
                # Retry-After（秒）があれば尊重
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
                else:
                    delay = self.backoff * (2 ** attempt)
                time.sleep(delay)
                attempt += 1
                continue

            # ここで最終判定
            if resp.status_code >= 400:
                self._handle_error(resp)
            return resp

    @staticmethod
    def _columns_to_params(columns: Sequence[str] | None) -> list[tuple[str, str]] | None:
        """
        文献取得APIは columns[] を繰り返しクエリで指定する仕様に合わせる。
        例: [('columns[]','app_doc_id'), ('columns[]','title')]
        """
        if not columns:
            return None
        return [("columns[]", c) for c in columns]

    # --- high-level methods ---
    def search_raw(self, payload: dict[str, Any]) -> dict[str, Any]:
        """検索API（POST /patents/search）への汎用ラッパー。payload はドキュメントの定義に従う。"""
        resp = self._request_with_retry("POST", "/patents/search", json=payload)
        return resp.json()

    def search_fulltext(
        self,
        q: str,
        *,
        columns: Sequence[str] | None = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """全文検索（search_type=fulltext）"""
        payload: dict[str, Any] = {"q": q, "search_type": "fulltext", "limit": limit}
        if columns is not None:
            payload["columns"] = list(columns)
        payload.update(kwargs)
        return self.search_raw(payload)

    def search_semantic(
        self,
        q: str,
        *,
        columns: Sequence[str] | None = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """セマンティック検索（search_type=semantic）"""
        payload: dict[str, Any] = {"q": q, "search_type": "semantic", "limit": limit}
        if columns is not None:
            payload["columns"] = list(columns)
        payload.update(kwargs)
        return self.search_raw(payload)

    def search_numbers(
        self,
        numbers: Sequence[tuple[str, str]],
        *,
        columns: Sequence[str] | None = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        番号一括検索。numbers は (番号, 型) のタプル列。
        例: [("JP2016057449A", "app_doc_id"), ("JP2019070899A", "app_doc_id")]
        """
        payload: dict[str, Any] = {"numbers": [{"n": n, "t": t} for n, t in numbers], "limit": limit}
        if columns is not None:
            payload["columns"] = list(columns)
        payload.update(kwargs)
        return self.search_raw(payload)

    def get_document(
        self,
        app_doc_id: str,
        *,
        columns: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """
        文献取得（GET /patents/{APP_DOC_ID}）
        columns は ['app_doc_id','title','top_claim'] 等。指定しない場合はサーバ側デフォルト。
        """
        params = self._columns_to_params(columns)
        resp = self._request_with_retry("GET", f"/patents/{app_doc_id}", params=params)
        return resp.json()

    def get_drawings(self, app_doc_id: str) -> list[str]:
        """図面リンクの取得（columns=['drawings']）"""
        data = self.get_document(app_doc_id, columns=["drawings"])
        record = data.get("record") or data
        return (record.get("drawings") or []) if isinstance(record, dict) else []


def load_images_from_drawing_urls(
    urls: Sequence[str],
    *,
    token: str | None = None,
    image_width: int | None = None,
    timeout: float = 30.0,
) -> list[Image.Image]:
    """
    Patentfieldの get_drawings() で得た画像URL群をダウンロードして PIL.Image のリストで返す。

    Args:
        urls: 画像URLのシーケンス
        token: 認証が必要な場合の API Token（"Token <token>" を自動付与）
        timeout: HTTP タイムアウト秒

    Returns:
        PIL.Image のリスト（順序は urls と同じ）
    """
    headers = {"User-Agent": "PatentfieldHttpxClient/0.1"}
    if token:
        headers["Authorization"] = f"Token {token}"

    images: list[Image.Image] = []
    # follow_redirects=True はストレージの署名付きURLなどのリダイレクト対策
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for url in urls:
            r = client.get(url)
            r.raise_for_status()

            # Bytes から安全に Image を作り、バッファ切断のため copy() しておく
            try:
                with Image.open(io.BytesIO(r.content)) as im:
                    im.load()          # データを強制ロード
                    if image_width:
                        im = im.resize((image_width, int(im.height * image_width / im.width)))
                    images.append(im.copy())
            except UnidentifiedImageError as e:
                raise ValueError(f"画像として解釈できませんでした: {url}") from e

    return images
