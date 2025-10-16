from typing import Any, Dict, Optional

from .http_client import HTTPClient, QuantumSDKError
from .models import Machine


class Client:
    def __init__(
        self,
        base_url: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        timeout_seconds: int = 10,
    ) -> None:
        self._http = HTTPClient(
            base_url=base_url,
            access_token=access_token,
            refresh_token=refresh_token,
            timeout_seconds=timeout_seconds,
        )

    def get_machine(self, machine_id: str) -> Machine:
        return Machine(http=self._http, machine_id=machine_id)

    # File APIs retained for convenience
    def save_file(self, machine_id: str, file_path: str, file_content) -> Dict[str, Any]:
        url = self._http._url("files/")
        files = {
            "file": (file_path, file_content, "application/form-data"),
        }
        data = {"machine": machine_id}
        # No machine_id here; caller should include it in multipart fields if needed
        headers = dict(self._http.session.headers)
        if "Content-Type" in headers:
            del headers["Content-Type"]
        resp = self._http.session.post(url, files=files, data=data, headers=headers, timeout=self._http._timeout)
        return self._http.handle(resp)

    def list_files(self, machine_id: str) -> Dict[str, Any]:
        url = self._http._url("files/")
        params = {"machine": machine_id}
        resp = self._http.request("GET", url, params=params)
        return self._http.handle(resp)

    def open_file(self, file_id: str) -> Dict[str, Any]:
        import requests

        url = self._http._url(f"files/{file_id}/")
        resp = self._http.request("GET", url)
        file_data = self._http.handle(resp)
        if isinstance(file_data, dict):
            file_url = file_data.get("full_path")
            if file_url:
                try:
                    file_resp = requests.get(file_url, timeout=self._http._timeout)
                    if file_resp.status_code == 200:
                        file_data["content"] = file_resp.content
                        file_data["content_type"] = file_resp.headers.get("Content-Type", "application/form-data")
                except Exception as exc:
                    file_data["content_error"] = f"Could not fetch file content: {exc}"
        return file_data

    # Temporary hardcoded - preserved
    def calibrate_coupler_idle_bias(self, machine_id: str, coupler_ids: list[int]) -> Dict[str, Any]:
        import requests

        if not isinstance(coupler_ids, list) or not coupler_ids:
            raise QuantumSDKError("coupler_ids must be a non-empty list of integers")
        try:
            coupler_ids_payload = [int(c) for c in coupler_ids]
        except Exception:
            raise QuantumSDKError("coupler_ids must contain integers only")
        url = "http://qeam-api-alb-1632396118.us-west-2.elb.amazonaws.com/calibrate/coupler-idle-bias"
        payload = {"machine_id": machine_id, "coupler_ids": coupler_ids_payload}
        resp = requests.post(url, json=payload, timeout=self._http._timeout)
        return self._http.handle(resp)


