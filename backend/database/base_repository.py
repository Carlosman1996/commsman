from abc import ABC, abstractmethod
from dataclasses import fields

from backend.models import DATACLASS_REGISTRY, BaseRequest


class BaseRepository(ABC):
    """Abstract repository for storing and retrieving items."""

    def __init__(self):
        self.selected_item = None

    @staticmethod
    def item_dict_to_dataclass(item_dict: dict) -> BaseRequest:
        cls_name = item_dict.get("item_handler")
        cls = DATACLASS_REGISTRY.get(cls_name)

        if cls is None:
            raise ValueError(f"Unknown item type: {cls_name}")

        # Ignore extra elemetns:
        valid_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in item_dict.items() if k in valid_fields}

        item = cls(**filtered_dict)  # Instantiate the dataclass
        return item

    def set_selected_item(self, item_uuid: str):
        self.selected_item = item_uuid

    def get_selected_item(self) -> BaseRequest:
        return self.get_item(self.selected_item)

    @abstractmethod
    def load(self):
        raise NotImplementedError
        pass

    @abstractmethod
    def save(self):
        raise NotImplementedError

    @abstractmethod
    def create_item(self, item_name: str, item_handler: str, parent_uuid: str = None, attribute: str = None) -> BaseRequest:
        raise NotImplementedError

    @abstractmethod
    def add_item(self, item: BaseRequest, attribute: str = None) -> BaseRequest:
        raise NotImplementedError

    @abstractmethod
    def update_item(self, item_uuid: str, **kwargs) -> BaseRequest:
        raise NotImplementedError

    @abstractmethod
    def replace_item(self, item_uuid: str, new_item: BaseRequest) -> BaseRequest:
        raise NotImplementedError

    @abstractmethod
    def get_item(self, item_uuid: str) -> BaseRequest:
        raise NotImplementedError

    @abstractmethod
    def get_items(self) -> dict[str, BaseRequest]:
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_uuid: str):
        raise NotImplementedError
