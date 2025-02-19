from abc import ABC, abstractmethod


class BaseHandler(ABC):
    @abstractmethod
    def connect(self):
        """Connect to the client."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the client."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        pass
