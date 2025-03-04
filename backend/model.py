import json
import os
from dataclasses import asdict

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

from backend.models import DATACLASS_REGISTRY
from backend.models.base import BaseItem
from utils.common import PROJECT_PATH


JSON_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.json")


class Model(QWidget):

    signal_model_update = pyqtSignal()

    def __init__(self, json_file_path: str = JSON_DATA_FILE):
        super().__init__()

        self.items = {}
        self.json_file_path = json_file_path
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

        with open(self.json_file_path, "w") as file:
            json.dump(items_dict, file)

        # Send update model signal:
        self.signal_model_update.emit()

    def create_item(self, item_name: str, item_handler: str, parent_uuid: str = None, attribute: str = None) -> BaseItem:
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent=parent_uuid)
        self.add_item(item, attribute)
        return self.items[item.uuid]

    def add_item(self, item: BaseItem, attribute: str = None) -> BaseItem:
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        self.items[item.uuid] = item
        if item.parent:
            if item.parent in self.items:
                # Save as attribute or as a child:
                if attribute:
                    self.update_item(item_uuid=item.parent, **{attribute: item.uuid})
                else:
                    self.items[item.parent].children.append(item.uuid)
            else:
                raise Exception(f"Item {item.parent} not found")
        print("add")
        self.save_to_json()
        return self.items[item.uuid]

    def update_item(self, item_uuid: str, **kwargs) -> BaseItem:
        """Actualiza un ítem existente y guarda cambios."""
        if item_uuid in self.items:
            for key, value in kwargs.items():
                setattr(self.items[item_uuid], key, value)
            print("update")
            self.save_to_json()
        else:
            raise Exception(f"Item {item_uuid} not found")
        return self.items[item_uuid]

    def replace_item(self, item_uuid: str, new_item: BaseItem) -> BaseItem:
        """Actualiza un ítem existente y guarda cambios."""
        if item_uuid != new_item.uuid:
            raise Exception(f"Items must have same uuid {item_uuid}, replace uuid {new_item.uuid}")

        if item_uuid in self.items:
            self.items[item_uuid] = new_item
            print("replace")
            self.save_to_json()
        else:
            raise Exception(f"Item {item_uuid} not found")
        return self.items[item_uuid]

    def delete_item(self, item_uuid: str):
        """Elimina un ítem y actualiza referencias. Luego, guarda los cambios."""
        if item_uuid in self.items:
            item = self.items.pop(item_uuid)
            if item.parent and item.parent in self.items:
                self.items[item.parent].children.remove(item_uuid)
            for child_uuid in item.children:
                if child_uuid in self.items:
                    self.delete_item(child_uuid)
            print("delete")
            self.save_to_json()
        else:
            raise Exception(f"Item {item_uuid} not found")

    def get_item(self, item_uuid: str) -> BaseItem:
        def _resolve_references(value, key: str = None):
            """Replace 'uuid_XXX' values with actual item references."""
            if key == "uuid" or key == "parent" or key == "children":
                return value

            if isinstance(value, str) and "uuid_" in value:
                return self.items.get(value)
            elif isinstance(value, list):
                return [_resolve_references(v) for v in value]
            elif isinstance(value, dict):
                return {k: _resolve_references(v, k) for k, v in value.items()}
            return value

        item = self.items.get(item_uuid)
        if item:
            # Resolve only first level references to complete necessary data. Parent and children will not be resolved:
            item_dict = _resolve_references(asdict(item))
            item = self.item_dict_to_dataclass(item_dict)

        return item

    def get_items(self):
        return self.items

    def set_selected_item(self, item_uuid: str):
        self.selected_item = item_uuid

    def get_selected_item(self) -> BaseItem:
        return self.get_item(self.selected_item)


if __name__ == "__main__":
    model_obj = Model()
    model_obj.load_from_json()
    print(model_obj.items)
    model_obj.save_to_json()
