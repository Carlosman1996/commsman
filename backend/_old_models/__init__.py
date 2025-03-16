import pkgutil
import importlib
import inspect
from backend._old_models.base import BaseRequest, BaseResult, Base


# Create a registry for dynamic loading
DATACLASS_REGISTRY = {"Base": Base, "BaseRequest": BaseRequest, "BaseResult": BaseResult}
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in Base.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseRequest.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseResult.__subclasses__()})
