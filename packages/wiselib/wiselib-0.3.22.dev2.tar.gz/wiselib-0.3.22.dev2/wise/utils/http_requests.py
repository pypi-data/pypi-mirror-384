from urllib.parse import urljoin

import requests
from time import perf_counter as time_now

from wise.utils.monitoring import HTTP_CLIENT_DURATION

DEFAULT_TIMEOUT = 60


class HTTPClient:
    def __init__(
        self,
        service_name: str,
        session: requests.Session | None = None,
        base_url: str | None = None,
    ):
        self.service_name = service_name
        self._client = session or requests.Session()
        self.base_url = base_url

    def request(self, method: str, url: str, _api_name: str = "unset", **kwargs):
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        start = time_now()
        success = "false"

        try:
            response = self._client.request(method, url, **kwargs)
            success = "true"
            return response
        finally:
            HTTP_CLIENT_DURATION.labels(
                self.service_name, _api_name, method, success
            ).observe(time_now() - start)

    def get(self, url: str, _api_name: str = "unset", **kwargs):
        return self.request("GET", self._get_url(url), _api_name=_api_name, **kwargs)

    def post(self, url: str, _api_name: str = "unset", **kwargs):
        return self.request("POST", self._get_url(url), _api_name=_api_name, **kwargs)

    def put(self, url: str, _api_name: str = "unset", **kwargs):
        return self.request("PUT", self._get_url(url), _api_name=_api_name, **kwargs)

    def patch(self, url: str, _api_name: str = "unset", **kwargs):
        return self.request("PATCH", self._get_url(url), _api_name=_api_name, **kwargs)

    def delete(self, url: str, _api_name: str = "unset", **kwargs):
        return self.request("DELETE", self._get_url(url), _api_name=_api_name, **kwargs)

    def __setattr__(self, key, value):
        if key in ["service_name", "_client"]:
            super().__setattr__(key, value)
        else:
            setattr(self._client, key, value)

    def __getattr__(self, item):
        return getattr(self._client, item)

    def _get_url(self, url: str) -> str:
        if not self.base_url:
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return urljoin(self.base_url, url)
