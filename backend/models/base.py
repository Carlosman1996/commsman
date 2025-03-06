from dataclasses import dataclass, field, fields

import uuid


@dataclass
class Base:
    name: str
    item_type: str
    item_handler: str = None
    uuid: str = field(default_factory=lambda: "uuid_" + str(uuid.uuid4()))

    def __post_init__(self):
        self.item_handler = self.__class__.__name__


@dataclass
class BaseRequest(Base):
    parent: str = None
    children: list[str] = field(default_factory=list)
    client: str = None
    client_type: str = "No connection"
    run_options: str = None
    last_result: str = None


@dataclass
class BaseResult(Base):
    parent: str = None
    children: list[str] = field(default_factory=list)
    client_type: str = None
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""
