import os
import pickle

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QIcon

from backend.base_client import BaseClient
from backend.custom_modbus_tcp_client import CustomModbusTcpClient
from frontend.common import ITEMS
from frontend.components.components import CustomStandardItemModel
from frontend.models.collection import Collection
from frontend.models.modbus import ModbusRequest
from utils.common import PROJECT_PATH

TREE_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.pkl")


class Item:
    def __init__(self, item_name: str = None, item_type: str = None):
        # TODO: create handler to automatically select dataclass depending on item_type
        if item_type == "Collection":
            self.dataclass = Collection(name=item_name, item_type=item_type)
        elif item_type == "Modbus":
            self.dataclass = ModbusRequest(name=item_name, item_type=item_type)
        else:
            raise NotImplementedError(f"Item type {item_type} not implemented")


class ModelItem(QStandardItem):
    def __init__(self, item):
        super().__init__(item.name)

        self.setData(item, Qt.ItemDataRole.UserRole)
        self.setIcon(QIcon(ITEMS[item.item_type]["icon_simple"]))
        self.setEditable(True)

    def __getattr__(self, name):
        if hasattr(self.data(Qt.ItemDataRole.UserRole), name):
            return getattr(self.data(Qt.ItemDataRole.UserRole), name)
        else:
            raise AttributeError(f"'ModelItem' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        item = self.data(Qt.ItemDataRole.UserRole)
        if hasattr(item, name):
            setattr(item, name, value)
            self.setData(item, Qt.ItemDataRole.UserRole)
        else:
            raise AttributeError(f"'ModelItem' object has no attribute '{name}'")


class ProtocolClientManager:
    def __init__(self):
        self.handlers: dict[str, BaseClient] = {}  # Key: handler ID, Value: handler

    def get_handler(self, protocol: str, **kwargs) -> BaseClient:
        """Get or create a handler for the specified protocol."""
        handler_id = self._generate_handler_id(protocol, **kwargs)
        if handler_id not in self.handlers:
            if protocol == "Modbus":
                if kwargs["client_type"] == "TCP":
                    self.handlers[handler_id] = CustomModbusTcpClient(kwargs["host"], kwargs["port"])
                else:
                    raise ValueError(f"Unsupported Modbus client type: {kwargs['client_type']}")
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
        return self.handlers[handler_id]

    def close_handler(self, protocol: str, **kwargs):
        """Close a handler for the specified protocol."""
        handler_id = self._generate_handler_id(protocol, **kwargs)
        if handler_id in self.handlers:
            self.handlers[handler_id].disconnect()
            del self.handlers[handler_id]

    def close_all_handlers(self):
        """Close a handler for the specified protocol."""
        for handler_client in self.handlers.values():
            handler_client.disconnect()

    def _generate_handler_id(self, protocol: str, **kwargs) -> str:
        """Generate a unique handler ID based on protocol and connection parameters."""
        handler_id = f"{protocol}"
        for key, value in kwargs.items():
            handler_id += f"_{key}_{value}"
        return handler_id

    def validate_handler(self, protocol: str, **kwargs) -> bool:
        """Check if a handler is valid (connected)."""
        handler_id = self._generate_handler_id(protocol, **kwargs)
        if handler_id in self.handlers:
            return self.handlers[handler_id].is_connected()
        return False

    def reconnect_handler(self, protocol: str, **kwargs):
        """Reset a handler if it’s invalid."""
        handler_id = self._generate_handler_id(protocol, **kwargs)
        if handler_id in self.handlers:
            self.handlers[handler_id].disconnect()
            del self.handlers[handler_id]
        return self.get_handler(protocol, **kwargs)


class Model(CustomStandardItemModel):

    signal_move_item = pyqtSignal(ModelItem)
    signal_update_item = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.protocol_client_manager = ProtocolClientManager()
        self.selected_item = None

    def set_selected_item(self, item):
        self.selected_item = item

    def get_selected_item(self):
        return self.selected_item

    def update_item(self, **kwargs):
        """Update the currently selected item with the provided fields."""
        if self.selected_item:
            for key, value in kwargs.items():
                if hasattr(self.selected_item, key):
                    setattr(self.selected_item, key, value)
                else:
                    raise ValueError(f"Item {self.selected_item} has not attribute {key}. Could not save value {value}")
        self.autosave_tree_data()
        self.signal_update_item.emit()

    def autosave_tree_data(self):
        data = self.serialize_tree()
        with open(TREE_DATA_FILE, "wb") as file:
            pickle.dump(data, file)

    def load_tree_data(self):
        """Load the tree structure from a pickle file."""
        try:
            with open(TREE_DATA_FILE, "rb") as file:
                data = pickle.load(file)
                self.deserialize_tree(data)
        except FileNotFoundError:
            pass  # No saved data available

    def serialize_tree(self):
        def serialize_item(item):
            return {
                "data": item.data(Qt.ItemDataRole.UserRole),
                "children": [serialize_item(item.child(i)) for i in range(item.rowCount())],
            }

        root_item = self.invisibleRootItem()
        return [serialize_item(root_item.child(i)) for i in range(root_item.rowCount())]

    def deserialize_tree(self, data):
        def deserialize_item(data, parent):
            item = ModelItem(data["data"])

            parent.appendRow(item)
            for child_data in data["children"]:
                deserialize_item(child_data, item)

        self.clear()
        self.setHorizontalHeaderLabels(["Items"])
        for item_data in data:
            deserialize_item(item_data, self.invisibleRootItem())
