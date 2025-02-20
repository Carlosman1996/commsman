from dataclasses import dataclass, field

from frontend.models.base import BaseResult
from frontend.models.run_options import RunOptions


@dataclass
class CollectionResult(BaseResult):
    name: str
    item_type: str = "Collection"
    parent: object = None
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""
    children: list = field(default_factory=list)
    total_ok: int = 0
    total_failed: int = 0
    total_pending: int = 0


@dataclass
class Collection:
    name: str
    item_type: str = "Collection"
    client_type: str = "No connection"
    client: dataclass = None
    run_options: RunOptions = None
    last_response: CollectionResult = None
