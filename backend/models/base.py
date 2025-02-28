from dataclasses import dataclass, field

import uuid


@dataclass
class BaseItem:
    name: str
    item_handler: str = None
    uuid: str = field(default_factory=lambda: "uuid_" + str(uuid.uuid4()))
    parent: str = None
    children: list[str] = field(default_factory=list)
    client_type: str = "No connection"
    client: str = None
    run_options: str = None
    last_result: str = None

    def __post_init__(self):
        self.item_handler = self.__class__.__name__


@dataclass
class BaseResult:
    name: str
    item_handler: str = None
    uuid: str = field(default_factory=lambda: "uuid_" + str(uuid.uuid4()))
    parent: str = None
    children: list[str] = field(default_factory=list)
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""

    def __post_init__(self):
        self.item_handler = self.__class__.__name__
