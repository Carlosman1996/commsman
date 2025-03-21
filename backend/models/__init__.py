from backend.models.base import Base, BaseItem, BaseRequest, BaseResult
from backend.models.request import Request
from backend.models.client import Client
from backend.models.collection import Collection, CollectionResult
from backend.models.modbus import ModbusTcpClient, ModbusRtuClient, ModbusRequest, ModbusResponse
from backend.models.run_options import RunOptions


# Create a registry for dynamic loading
DATACLASS_REGISTRY = {"BaseItem": BaseItem, "BaseRequest": BaseRequest, "BaseResult": BaseResult}
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseItem.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseRequest.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseResult.__subclasses__()})
