from abc import ABC, abstractmethod

from backend.models import DATACLASS_REGISTRY, BaseItem, BaseRequest


class BaseRepository(ABC):
    """Abstract repository for storing and retrieving items."""

    def __init__(self):
        self.selected_item: int | None = None

    @staticmethod
    def get_class_handler(item_handler: str):
        cls = DATACLASS_REGISTRY.get(item_handler)
        if cls is None:
            raise ValueError(f"Unknown item handler: {item_handler}")
        return cls

    def set_selected_item(self, item_id: int):
        self.selected_item = item_id

    def get_selected_item(self) -> BaseRequest | None:
        if self.selected_item:
            return self.get_item_request(item_id=self.selected_item)
        else:
            return None

    @abstractmethod
    def load(self):
        raise NotImplementedError

    @abstractmethod
    def save(self):
        raise NotImplementedError

    @abstractmethod
    def create_item_request_from_handler(self, item_name: str, item_handler: str, parent: int):
        raise NotImplementedError

    @abstractmethod
    def add_item_from_dataclass(self, item: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def create_client_item(self, item_name: str, item_handler: str, parent: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def create_run_options_item(self, item_name: str, item_handler: str, parent: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def get_item_request(self, item_id: int):
        raise NotImplementedError

    @abstractmethod
    def get_item_last_result_tree(self, item_id: BaseItem):
        raise NotImplementedError

    @abstractmethod
    def get_items_request_tree(self, item_id: int):
        raise NotImplementedError

    @abstractmethod
    def update_item_from_handler(self, item_id: int, item_handler: str, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_id: int):
        raise NotImplementedError
