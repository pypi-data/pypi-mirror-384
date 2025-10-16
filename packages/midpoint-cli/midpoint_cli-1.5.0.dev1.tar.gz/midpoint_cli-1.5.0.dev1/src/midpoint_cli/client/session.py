import typing

from requests.adapters import HTTPAdapter
from urllib3 import Retry

from midpoint_cli.client import MidpointCommunicationObserver


class CustomRetryManager(Retry):
    def __init__(self, observer: MidpointCommunicationObserver, **kwargs):
        self._observer = observer
        super().__init__(**kwargs)

    def get_backoff_time(self):
        return 2

    def new(self, **kw: typing.Any) -> 'CustomRetryManager':
        result = super().new(observer=self._observer, **kw)
        return result

    def increment(self, *args, **kwargs) -> 'CustomRetryManager':
        self._observer.on_http_error()
        return super().increment(*args, **kwargs)


class CustomHTTPAdapter(HTTPAdapter):
    def __init__(self, observer: MidpointCommunicationObserver, **kwargs):
        super().__init__(**kwargs)
        self._observer = observer

    def send(self, request, **kwargs):
        self._observer.on_http_call()
        response = super().send(request, **kwargs)
        self._observer.on_http_success()
        return response
