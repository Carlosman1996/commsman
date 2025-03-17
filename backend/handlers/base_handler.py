from abc import ABC, abstractmethod


class BaseHandler(ABC):
    @abstractmethod
    def connect(self):
        """Connect to the client."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        """Disconnect from the client."""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        raise NotImplementedError

    def execute_request(self, **kwargs):
        raise NotImplementedError
