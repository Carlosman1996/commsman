import pkgutil
import importlib
import inspect
from backend.models.base import BaseRequest, BaseResult, Base

# Dynamically import all modules in the package
__all__ = []  # Keep track of the imported dataclasses

for _, module_name, _ in pkgutil.iter_modules(__path__, __name__ + "."):
    module = importlib.import_module(module_name)

    # Find all dataclasses that inherit from BaseModel
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseRequest) and obj is not BaseRequest:
            globals()[name] = obj  # Make available at package level
            __all__.append(name)

# Create a registry for dynamic loading
DATACLASS_REGISTRY = {"Base": Base, "BaseRequest": BaseRequest, "BaseResult": BaseResult}
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in Base.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseRequest.__subclasses__()})
DATACLASS_REGISTRY.update({cls.__name__: cls for cls in BaseResult.__subclasses__()})
