from dataclasses import dataclass

from backend.models.base import BaseItem


@dataclass
class RunOptions(BaseItem):
    item_type: str = "RunOptions"
    polling: bool = False
    polling_interval: int = 1
    delayed_start: int = 0
