from dataclasses import dataclass, field

from backend.models.base import BaseResult, BaseItem


@dataclass
class CollectionResult(BaseResult):
    total_ok: int = 0
    total_failed: int = 0
    total_pending: int = 0


@dataclass
class Collection(BaseItem):
    pass
