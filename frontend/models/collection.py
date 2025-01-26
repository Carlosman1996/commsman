from dataclasses import dataclass


@dataclass
class Collection:
    name: str
    type: str = "Collection"
