import json
import os
from dataclasses import asdict

from backend.repository.base_repository import BaseRepository
from backend.models import DATACLASS_REGISTRY, BaseRequest
from config import PROJECT_PATH


JSON_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.json")


class JsonRepository(BaseRepository):

    def __init__(self, json_file_path: str = JSON_DATA_FILE):
        super().__init__()

        self.items = {}
        self.json_file_path = json_file_path
        self.selected_item = None
        self.load()

    def item_dict_to_dataclass(self, item_dict: dict):
        cls = self.get_class_handler(item_dict.get("item_handler"))

        # Ignore extra elemetns:
        valid_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in item_dict.items() if k in valid_fields}

        item = cls(**filtered_dict)  # Instantiate the dataclass
        return item

    def load(self):
        # Open and read the JSON file
        with open(self.json_file_path, 'r') as file:
            data = json.load(file)

        for item_uuid, item_info in data.items():
            item = self.item_dict_to_dataclass(item_info)
            self.items[item_uuid] = item

    def save(self):
        items_dict = {}
        for item_uuid, item_dataclass in self.items.items():
            items_dict[item_uuid] = asdict(item_dataclass)

        with open(self.json_file_path, "w") as file:
            json.dump(items_dict, file)

    def create_item(self, item_name: str, item_handler: str, parent_uuid: str = None, attribute: str = None) -> BaseRequest:
        """Agrega un nuevo ítem al almacenamiento y guarda cambios."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent=parent_uuid)
        self.add_item(item, attribute)
        return self.items[item.uuid]

    def add_item(self, item: BaseRequest, attribute: str = None) -> BaseRequest:
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
        self.save()
        return self.items[item.uuid]

    def update_item(self, item_uuid: str, **kwargs) -> BaseRequest:
        """Actualiza un ítem existente y guarda cambios."""
        if item_uuid in self.items:
            for key, value in kwargs.items():
                setattr(self.items[item_uuid], key, value)
            self.save()
        else:
            raise Exception(f"Item {item_uuid} not found")
        return self.items[item_uuid]

    def replace_item(self, item_uuid: str, new_item: BaseRequest) -> BaseRequest:
        """Actualiza un ítem existente y guarda cambios."""
        if item_uuid != new_item.uuid:
            raise Exception(f"Items must have same uuid {item_uuid}, replace uuid {new_item.uuid}")

        if item_uuid in self.items:
            self.items[item_uuid] = new_item
            self.save()
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
            self.save()
        else:
            raise Exception(f"Item {item_uuid} not found")

    def get_item(self, item_uuid: str) -> BaseRequest:
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

    def get_items(self) -> dict[str, BaseRequest]:
        return self.items

if __name__ == "__main__":
    model_obj = JsonRepository()
    model_obj.load()
    print(model_obj.items)
    model_obj.save()
