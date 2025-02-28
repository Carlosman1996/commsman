import json
import os
from dataclasses import asdict, is_dataclass

from backend.models import DATACLASS_REGISTRY
from backend.models.base import BaseItem
from backend.models.collection import Collection
from backend.models.modbus import ModbusRequest, ModbusTcpClient, ModbusRtuClient
from backend.models.run_options import RunOptions
from utils.common import PROJECT_PATH


JSON_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.json")


class Model:
    def __init__(self, json_file_path: str = JSON_DATA_FILE):
        self.items = {}
        self.json_file_path = json_file_path
        self.json_file_path_save = os.path.join(PROJECT_PATH, "project_structure_data_save.json")
        self.selected_item = None

    def load_from_json_old_structure(self, data: str | dict = None, parent=None):
        if isinstance(data, str):
            # Open and read the JSON file
            with open(data, 'r') as file:
                data = json.load(file)

        uuids = []
        for item in data:
            item_data = item["data"]

            if "run_options" in item_data and isinstance(item_data["run_options"], dict):
                del item_data["run_options"]["item_type"]
                item_dataclass = RunOptions(**item_data["run_options"])
                item_data["run_options"] = item_dataclass.uuid
                self.items[item_dataclass.uuid] = item_dataclass

            if "client" in item_data and isinstance(item_data["client"], dict):
                del item_data["client"]["item_type"]
                if "host" in item_data["client"]:
                    item_dataclass = ModbusTcpClient(**item_data["client"])
                    item_data["client"] = item_dataclass.uuid
                    self.items[item_dataclass.uuid] = item_dataclass
                elif "baudrate" in item_data["client"]:
                    item_dataclass = ModbusRtuClient(**item_data["client"])
                    item_data["client"] = item_dataclass.uuid
                    self.items[item_dataclass.uuid] = item_dataclass

            if item_data["item_type"] == "Collection":
                del item_data["item_type"]
                item_dataclass = Collection(**item_data)
            elif item_data["item_type"] == "Modbus":
                del item_data["item_type"]
                item_dataclass = ModbusRequest(**item_data)
            else:
                raise NotImplementedError(f"Item type {item_data["item_handler"]} not implemented")

            item_dataclass.children = self.load_from_json_old_structure(item["children"], item_dataclass)
            if parent:
                item_dataclass.parent = parent.uuid

            uuids.append(item_dataclass.uuid)
            self.items[item_dataclass.uuid] = item_dataclass
        return uuids

    def _item_dict_to_dataclass(self, item_dict: dict) -> BaseItem:
        cls_name = item_dict.get("item_handler")
        cls = DATACLASS_REGISTRY.get(cls_name)

        if cls is None:
            raise ValueError(f"Unknown item type: {cls_name}")

        item = cls(**item_dict)  # Instantiate the dataclass
        return item

    def load_from_json(self):
        # Open and read the JSON file
        with open(self.json_file_path, 'r') as file:
            data = json.load(file)

        for item_uuid, item_info in data.items():
            item = self._item_dict_to_dataclass(item_info)
            self.items[item_uuid] = item

    def save_to_json(self):
        items_dict = {}
        for item_uuid, item_dataclass in self.items.items():
            items_dict[item_uuid] = asdict(item_dataclass)

        with open(self.json_file_path_save, "w") as file:
            json.dump(items_dict, file)

    def update_item(self, item: BaseItem, **kwargs):
        """Update item with the provided fields."""
        if item.uuid not in self.items:
            raise ValueError(f"Item {item} not in database")

        for key, value in kwargs.items():
            if hasattr(item, key):
                if is_dataclass(value) or isinstance(value, dict):
                    raise ValueError(f"Value {value} type not allowed")
                elif isinstance(value, list) and any([is_dataclass(item) or isinstance(item, dict) for item in value]):
                    raise ValueError(f"Value {value} subtypes not allowed")
                setattr(self.items[item.uuid], key, value)
            else:
                raise ValueError(f"Item {item} has not attribute {key}. Could not save value {value}")

        self.save_to_json()

    def add_item(self, item: BaseItem):
        self.items[item.uuid] = item

    def _resolve_references(self, value, key: str = None):
        """Recursively replace 'uuid_XXX' values with actual item references."""
        if key == "uuid" or key == "parent" or key == "children":
            return value

        if isinstance(value, str) and "uuid_" in value:
            return self.items.get(value)
        elif isinstance(value, list):
            return [self._resolve_references(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._resolve_references(v, k) for k, v in value.items()}
        return value

    def get_item(self, item_uuid: str) -> BaseItem:
        item = self.items.get(item_uuid)
        if item:
            item_dict = asdict(item)
            item_dict = self._resolve_references(item_dict)
            item = self._item_dict_to_dataclass(item_dict)
        return item

    def set_selected_item(self, item_uuid: str):
        self.selected_item = item_uuid

    def get_selected_item(self) -> BaseItem:
        return self.get_item(self.selected_item)

    def get_items(self, items_uuid: list[str]) -> list[BaseItem]:
        items = []
        for item_uuid in items_uuid:
            items.append(self.get_item(item_uuid))
        return items

    def get_item_parent(self, item_uuid: str) -> BaseItem:
        item = self.get_item(item_uuid)
        return self.get_item(item.parent)

    def get_item_children(self, item_uuid: str) -> list[BaseItem]:
        item = self.get_item(item_uuid)
        return self.get_items(item.children)


if __name__ == "__main__":
    model_obj = Model()
    # model_obj.load_from_json()
    model_obj.load_from_json_old_structure(os.path.join(PROJECT_PATH, "old_project_structure_data.json"))
    print(model_obj.items)
    model_obj.save_to_json()
