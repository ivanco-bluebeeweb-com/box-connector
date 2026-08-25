"""Thin Box Platform API v2.0 REST client (Client Credentials Grant / Service Account).

Auth model: OAuth2 client_credentials with box_subject_type=enterprise --
authenticates as the enterprise's auto-provisioned Service Account. The
access-token cache below follows the same fix applied portfolio-wide for
Vikunja #2356 (client-credentials connectors not caching tokens between
calls).
"""
from __future__ import annotations

import time
from typing import Any

import httpx

_API_BASE = "https://api.box.com/2.0"
_UPLOAD_BASE = "https://upload.box.com/api/2.0"
_TOKEN_URL = "https://api.box.com/oauth2/token"


class BoxError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class BoxClient:
    """REST client for the Box Platform API, scoped to one enterprise."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        enterprise_id: str,
        *,
        as_user_id: str = "",
        timeout: float = 30.0,
    ):
        if not client_id or not client_secret:
            raise BoxError("Client ID and Client Secret are required.")
        eid = (enterprise_id or "").strip()
        if not eid:
            raise BoxError("Enterprise ID is required.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.enterprise_id = eid
        self.as_user_id = (as_user_id or "").strip()
        self.timeout = timeout
        self._access_token = ""
        self._token_expiry = 0.0

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry - 30:
            return self._access_token
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "box_subject_type": "enterprise",
            "box_subject_id": self.enterprise_id,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(_TOKEN_URL, data=data)
            except httpx.RequestError as exc:
                raise BoxError(f"Could not reach Box: {exc}", retryable=True) from exc
            if resp.status_code != 200:
                detail = ""
                try:
                    detail = resp.json().get("error_description", "")[:200]
                except Exception:  # noqa: BLE001
                    pass
                raise BoxError(
                    f"Authentication failed ({resp.status_code}): {detail or 'check client id/secret/enterprise id'}"
                )
            payload = resp.json()
            self._access_token = payload.get("access_token", "")
            self._token_expiry = time.time() + float(payload.get("expires_in", 3600))
            if not self._access_token:
                raise BoxError("Authentication succeeded but no access_token was returned.")
            return self._access_token

    def _as_user_headers(self) -> dict:
        return {"As-User": self.as_user_id} if self.as_user_id else {}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        query: dict | None = None,
        json_body: dict | None = None,
        extra_headers: dict | None = None,
        content_type: str | None = None,
    ) -> Any:
        """Make a Box API request. path may be a full URL or a /-prefixed relative path."""
        token = await self._ensure_token()
        url = path if path.startswith("http") else f"{_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        headers.update(self._as_user_headers())
        if content_type:
            headers["Content-Type"] = content_type
        if extra_headers:
            headers.update(extra_headers)
        q = query if query is not None else params
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(method, url, params=q, json=json_body, headers=headers)
            except httpx.RequestError as exc:
                raise BoxError(f"Could not reach Box: {exc}", retryable=True) from exc
        return await self._handle_response(resp)

    async def download(self, file_id: str) -> bytes:
        """Download a file's raw bytes via the content endpoint."""
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"}
        headers.update(self._as_user_headers())
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(f"{_API_BASE}/files/{file_id}/content", headers=headers)
            except httpx.RequestError as exc:
                raise BoxError(f"Could not reach Box: {exc}", retryable=True) from exc
        if resp.status_code >= 400:
            await self._handle_response(resp)
        return resp.content

    async def upload(self, filename: str, parent_folder_id: str, content: bytes, file_id: str = "") -> dict:
        """Upload a new file (file_id empty) or a new version of an existing file."""
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"}
        headers.update(self._as_user_headers())
        if file_id:
            url = f"{_UPLOAD_BASE}/files/{file_id}/content"
            attrs = {"name": filename}
        else:
            url = f"{_UPLOAD_BASE}/files/content"
            attrs = {"name": filename, "parent": {"id": parent_folder_id}}
        import json as _json
        files = {
            "attributes": (None, _json.dumps(attrs), "application/json"),
            "file": (filename, content, "application/octet-stream"),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, headers=headers, files=files)
            except httpx.RequestError as exc:
                raise BoxError(f"Could not reach Box upload service: {exc}", retryable=True) from exc
        data = await self._handle_response(resp)
        entries = (data or {}).get("entries", [])
        return entries[0] if entries else (data or {})

    async def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "a few")
            raise BoxError(f"Rate limited by Box. Retry after {retry_after}s.", retryable=True)
        if resp.status_code >= 400:
            detail = ""
            try:
                body = resp.json()
                detail = body.get("message") or body.get("error_description") or str(body)[:300]
            except Exception:  # noqa: BLE001
                detail = resp.text[:300]
            raise BoxError(f"Box error {resp.status_code}: {detail}")
        if resp.status_code == 204 or not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {}
