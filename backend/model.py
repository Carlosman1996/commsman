import json
import os
from dataclasses import asdict

from backend.models import DATACLASS_REGISTRY
from backend.models.base import BaseItem
from utils.common import PROJECT_PATH


JSON_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.json")


class Model:
    def __init__(self, json_file_path: str = JSON_DATA_FILE):
        self.items = {}
        self.json_file_path = json_file_path
        self.json_file_path_save = os.path.join(PROJECT_PATH, "project_structure_data_save.json")
        self.selected_item = None
        self.load_from_json()

    def item_dict_to_dataclass(self, item_dict: dict) -> BaseItem:
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
            item = self.item_dict_to_dataclass(item_info)
            self.items[item_uuid] = item

    def save_to_json(self):
        items_dict = {}
        for item_uuid, item_dataclass in self.items.items():
            items_dict[item_uuid] = asdict(item_dataclass)

        with open(self.json_file_path_save, "w") as file:
            json.dump(items_dict, file)

    def create_item(self, item_name: str, item_type: str, parent_uuid: str = None):
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        if item_type == "Collection":
            item = DATACLASS_REGISTRY.get("Collection")(name=item_name, item_type=item_type, parent=parent_uuid)
        elif item_type == "Modbus":
            item = DATACLASS_REGISTRY.get("ModbusRequest")(name=item_name, item_type=item_type, parent=parent_uuid)
        else:
            raise NotImplementedError(f"Item type {item_type} not implemented")

        self.add_item(item)

    def add_item(self, item: BaseItem):
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        self.items[item.uuid] = item
        if item.parent and item.parent in self.items:
            self.items[item.parent].children.append(item.uuid)
        self.save_to_json()

    def add_item_run_options(self, item_uuid: str, item_name: str) -> BaseItem:
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        run_options_item = DATACLASS_REGISTRY.get("RunOptions")(name=item_name, parent=item_uuid)
        self.items[run_options_item.uuid] = run_options_item
        self.items[item_uuid].run_options = run_options_item.uuid
        self.save_to_json()
        return run_options_item

    def add_item_client(self, item_uuid: str, item_handler: str, item_name: str) -> BaseItem:
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        client_item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent=item_uuid)
        self.items[client_item.uuid] = client_item
        self.items[item_uuid].client = client_item.uuid
        self.save_to_json()
        return client_item

    def update_item(self, item_uuid: str, **kwargs):
        """Actualiza un ítem existente y guarda cambios."""
        if item_uuid in self.items:
            for key, value in kwargs.items():
                setattr(self.items[item_uuid], key, value)
            self.save_to_json()

    def delete_item(self, item_uuid: str):
        """Elimina un ítem y actualiza referencias. Luego, guarda los cambios."""
        if item_uuid in self.items:
            item = self.items.pop(item_uuid)
            if item.parent and item.parent in self.items:
                self.items[item.parent].children.remove(item_uuid)
            for child_uuid in item.children:
                if child_uuid in self.items:
                    self.items.pop(child_uuid)
            self.save_to_json()

    def _resolve_references(self, value, key: str = None):
        """Replace 'uuid_XXX' values with actual item references."""
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
            # Resolve only first level references to complete necessary data. Parent and children will not be resolved:
            item_dict = asdict(item)
            item_dict = self._resolve_references(item_dict)
            item = self.item_dict_to_dataclass(item_dict)
        return item

    def get_items(self, items_uuid: list[str]) -> list[BaseItem]:
        items = []
        for item_uuid in items_uuid:
            items.append(self.get_item(item_uuid))
        return items

    def set_selected_item(self, item_uuid: str):
        self.selected_item = item_uuid

    def get_selected_item(self) -> BaseItem:
        return self.get_item(self.selected_item)

    def get_item_parent(self, item_uuid: str) -> BaseItem:
        item = self.get_item(item_uuid)
        return self.get_item(item.parent)

    def get_item_children(self, item_uuid: str) -> list[BaseItem]:
        item = self.get_item(item_uuid)
        return self.get_items(item.children)


if __name__ == "__main__":
    model_obj = Model()
    model_obj.load_from_json()
    print(model_obj.items)
    model_obj.save_to_json()
