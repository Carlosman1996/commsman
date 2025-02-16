from dataclasses import dataclass


@dataclass
class RunOptions:
    name: str
    polling: bool = False
    polling_interval: int = 1
    delayed_start: int = 0
