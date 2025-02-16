from dataclasses import dataclass

from frontend.models.run_options import RunOptions


@dataclass
class Collection:
    name: str
    item_type: str = "Collection"
    client_type: str = "No connection"
    client: dataclass = None
    run_options: RunOptions = None
