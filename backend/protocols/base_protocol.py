from abc import ABC, abstractmethod

from PyQt6.QtCore import pyqtSignal


class BaseProtocol(ABC):
    @abstractmethod
    def connect(self, *args, **kwargs):
        """Establece conexión con el dispositivo"""
        pass

    @abstractmethod
    def execute_request(self, *args, **kwargs):
        """Execute request"""
        pass

    @abstractmethod
    def disconnect(self):
        """Cierra la conexión"""
        pass
