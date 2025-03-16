from dataclasses import dataclass

from backend._old_models.base import Base


@dataclass
class RunOptions(Base):
    item_type: str = "RunOptions"
    polling: bool = False
    polling_interval: int = 1
    delayed_start: int = 0
