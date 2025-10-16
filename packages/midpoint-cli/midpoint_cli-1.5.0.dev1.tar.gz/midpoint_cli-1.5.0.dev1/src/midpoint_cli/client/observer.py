from abc import ABC, abstractmethod


class MidpointCommunicationObserver(ABC):
    @abstractmethod
    def on_http_call(self):
        pass

    @abstractmethod
    def on_http_error(self):
        pass

    @abstractmethod
    def on_http_success(self):
        pass


class NopMidpointCommunicationObserver(MidpointCommunicationObserver):
    def on_http_call(self):
        pass

    def on_http_error(self):
        pass

    def on_http_success(self):
        pass
