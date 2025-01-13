from abc import ABC, abstractmethod


class BaseProtocol(ABC):
    @abstractmethod
    def connect(self, *args, **kwargs):
        """Establece conexión con el dispositivo"""
        pass

    @abstractmethod
    def read(self, *args, **kwargs):
        """Lee datos desde el dispositivo"""
        pass

    @abstractmethod
    def write(self, *args, **kwargs):
        """Escribe datos en el dispositivo"""
        pass

    @abstractmethod
    def disconnect(self):
        """Cierra la conexión"""
        pass
