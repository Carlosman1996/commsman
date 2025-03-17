from abc import ABC, abstractmethod
from dataclasses import fields

from backend.models import DATACLASS_REGISTRY, BaseItem, BaseRequest, BaseResult, Item


class BaseRepository(ABC):
    """Abstract repository for storing and retrieving items."""

    def __init__(self):
        self.selected_item = None

    @staticmethod
    def get_class_handler(item_handler: str):
        cls = DATACLASS_REGISTRY.get(item_handler)
        if cls is None:
            raise ValueError(f"Unknown item handler: {item_handler}")
        return cls

    def item_dict_to_dataclass(self, item_dict: dict):
        cls = self.get_class_handler(item_dict.get("item_handler"))

        # Ignore extra elemetns:
        valid_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in item_dict.items() if k in valid_fields}

        item = cls(**filtered_dict)  # Instantiate the dataclass
        return item

    def create_item_dataclass(self, item_handler: str, **kwargs):
        cls = self.get_class_handler(item_handler)
        item_dataclass = cls(**kwargs)
        return item_dataclass

    def set_selected_item(self, item: Item):
        self.selected_item = item

    def get_selected_item(self):
        return self.get_item_request(self.selected_item)

    @abstractmethod
    def load(self):
        raise NotImplementedError

    @abstractmethod
    def save(self):
        raise NotImplementedError

    @abstractmethod
    def create_item_from_handler(self, item_name: str, item_handler: str, parent: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def create_item_from_dataclass(self, item: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def create_client_item(self, item_name: str, item_handler: str, parent: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def create_run_options_item(self, item_name: str, item_handler: str, parent: BaseItem):
        raise NotImplementedError

    # @abstractmethod
    # def add_item(self, item: BaseItem, attribute: str = None):
    #     raise NotImplementedError

    @abstractmethod
    def update_item(self, item: BaseItem, **kwargs):
        raise NotImplementedError

    # @abstractmethod
    # def replace_item(self, item: BaseItem, new_item: BaseItem):
    #     raise NotImplementedError

    @abstractmethod
    def get_item_request(self, item: Item):
        raise NotImplementedError

    # @abstractmethod
    # def get_items(self) -> dict[str, BaseItem]:
    #     raise NotImplementedError

    @abstractmethod
    def delete_item(self, item: Item):
        raise NotImplementedError
