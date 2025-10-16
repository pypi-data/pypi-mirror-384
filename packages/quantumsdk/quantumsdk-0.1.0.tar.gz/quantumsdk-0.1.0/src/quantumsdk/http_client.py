from typing import Any, Dict, Optional

import requests
from urllib.parse import urlparse


class QuantumSDKError(Exception):
    pass


class HTTPClient:
    def __init__(
        self,
        base_url: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        timeout_seconds: int = 10,
    ) -> None:
        if not base_url:
            raise QuantumSDKError("Base URL is required.")
        if not access_token:
            raise QuantumSDKError("Access token is required.")

        self._base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._timeout = timeout_seconds

        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self._base_url}/{path}"

    def _ensure_allowed_url(self, url: str) -> str:
        base = urlparse(self._base_url)
        target = urlparse(url)
        if not target.scheme or not target.netloc:
            normalized = self._url(target.path or "")
            target = urlparse(normalized)
        if target.username or target.password:
            raise QuantumSDKError("Egress blocked: credentials in URL are not allowed")
        if (target.scheme, target.hostname, target.port or (443 if target.scheme == "https" else 80)) != (
            base.scheme,
            base.hostname,
            base.port or (443 if base.scheme == "https" else 80),
        ):
            raise QuantumSDKError("URL host is not allowed")
        return target.geturl()

    def _refresh_tokens(self) -> None:
        if not self._refresh_token:
            raise QuantumSDKError("Refresh token is not configured.")
        url = self._url("auth/refresh_token/")
        resp = self.session.post(
            url,
            json={"refresh": self._refresh_token},
            timeout=self._timeout,
            allow_redirects=False,
        )
        if resp.status_code != 200:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise QuantumSDKError(f"Token refresh failed: HTTP {resp.status_code}: {detail}")

        data = resp.json()
        payload = data.get("data") if isinstance(data, dict) else None
        if not isinstance(payload, dict):
            raise QuantumSDKError("Token refresh failed: unexpected response shape")
        new_access = payload.get("access")
        new_refresh = payload.get("refresh")
        if not new_access or not new_refresh:
            raise QuantumSDKError("Token refresh failed: 'access' token missing in response")
        self._access_token = new_access
        self._refresh_token = new_refresh
        self.session.headers.update({"Authorization": f"Bearer {self._access_token}"})

    def request(self, method: str, path_or_url: str, **kwargs: Any) -> requests.Response:
        headers: Dict[str, str] = dict(kwargs.get("headers") or {})
        if "Authorization" in headers:
            headers["Authorization"] = f"Bearer {self._access_token}"
            kwargs["headers"] = headers
        url = self._ensure_allowed_url(path_or_url)
        kwargs.setdefault("allow_redirects", False)
        resp = self.session.request(method, url, timeout=self._timeout, **kwargs)
        if resp.status_code == 401:
            self._refresh_tokens()
            headers = dict(kwargs.get("headers") or {})
            headers["Authorization"] = f"Bearer {self._access_token}"
            kwargs["headers"] = headers
            resp = self.session.request(method, url, timeout=self._timeout, **kwargs)
        return resp

    def handle(self, resp: requests.Response) -> Any:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise QuantumSDKError(f"HTTP {resp.status_code}: {detail}")
        if resp.status_code == 204:
            return None
        try:
            data = resp.json()
        except Exception:
            return resp.text

        if isinstance(data, dict) and "success" in data:
            if data.get("success") is True:
                return data.get("data", data)
            # error branch (should have been caught by status_code) but handle anyway
            error_payload = data.get("error", data)
            raise QuantumSDKError(f"Request failed: {error_payload}")
        return data


