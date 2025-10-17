from typing import Any, Callable
from datetime import datetime

from pytz import UTC
import requests

from .errors import ResponseError

API_BASE_URL = "https://api.gradient-labs.ai"
USER_AGENT = "Gradient Labs Python"


class HttpClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = API_BASE_URL,
        timeout: int = None,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def post(self, path: str, body: Any):
        return self._api_call(requests.post, path, body)

    def put(self, path: str, body: Any):
        return self._api_call(requests.put, path, body)

    def get(self, path: str, body: Any):
        return self._api_call(requests.get, path, body)

    def delete(self, path: str, body: Any):
        return self._api_call(requests.delete, path, body)

    @classmethod
    def localize(cls, timestamp: datetime) -> str:
        return UTC.localize(timestamp).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _api_call(self, request_func: Callable, path: str, body: Any):
        url = f"{self.base_url}/{path}"
        rsp = request_func(
            url,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": USER_AGENT,
            },
            timeout=self.timeout,
        )

        if rsp.status_code < 200 or rsp.status_code > 299:
            raise ResponseError(rsp)
        if len(rsp.content) != 0:
            return rsp.json()
