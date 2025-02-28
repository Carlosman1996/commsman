from dataclasses import dataclass

from backend.models import BaseItem


@dataclass
class RunOptions(BaseItem):
    name: str
    polling: bool = False
    polling_interval: int = 1
    delayed_start: int = 0
