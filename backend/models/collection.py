from dataclasses import dataclass

from backend.models.base import BaseResult, BaseItem


@dataclass
class CollectionResult(BaseResult):
    item_type: str = "Collection"
    total_ok: int = 0
    total_failed: int = 0
    total_pending: int = 0


@dataclass
class Collection(BaseItem):
    item_type: str = "Collection"
