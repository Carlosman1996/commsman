from dataclasses import dataclass


@dataclass
class Collection:
    name: str
    item_type: str = "Collection"
    client_type: str = "No connection"
    client: dataclass = None
