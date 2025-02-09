from dataclasses import dataclass


@dataclass
class Collection:
    name: str
    item_type: str = "Collection"
    connection_client: dataclass = None
