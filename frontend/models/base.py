from dataclasses import dataclass


@dataclass
class BaseResult:
    name: str
    item_type: str = None
    parent: object = None
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""
