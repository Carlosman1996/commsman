import os
import pickle

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QIcon, QStandardItemModel
from PyQt6.QtWidgets import QMessageBox

from frontend.common import ITEMS
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


class CustomStandardItem(QStandardItem):
    def __init__(self, item):
        super().__init__(item.name)

        self.setData(item, Qt.ItemDataRole.UserRole)
        self.setIcon(QIcon(ITEMS[item.item_type]["icon_simple"]))
        self.setEditable(True)

    def __getattr__(self, name):
        if hasattr(self.data(Qt.ItemDataRole.UserRole), name):
            return getattr(self.data(Qt.ItemDataRole.UserRole), name)
        else:
            raise AttributeError(f"'CustomStandardItem' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        item = self.data(Qt.ItemDataRole.UserRole)
        if hasattr(item, name):
            setattr(item, name, value)
            self.setData(item, Qt.ItemDataRole.UserRole)
        else:
            raise AttributeError(f"'CustomStandardItem' object has no attribute '{name}'")


class Model(QStandardItemModel):

    signal_move_item = pyqtSignal(CustomStandardItem)

    def __init__(self):
        super().__init__()
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
            item = CustomStandardItem(data["data"])

            parent.appendRow(item)
            for child_data in data["children"]:
                deserialize_item(child_data, item)

        self.clear()
        self.setHorizontalHeaderLabels(["Items"])
        for item_data in data:
            deserialize_item(item_data, self.invisibleRootItem())

    def move_to_destination(self, source_index, destination_index):
        """Move an item to the exact drop location with restrictions."""
        if not source_index.isValid():
            return

        source_item = self.itemFromIndex(source_index)
        source_parent = source_item.parent() or self.invisibleRootItem()
        source_row = source_item.row()

        if destination_index.isValid():
            destination_item = self.itemFromIndex(destination_index)
            destination_parent = destination_item.parent() or self.invisibleRootItem()
            destination_row = destination_index.row()
        else:
            # Dropping to the root
            destination_item = self.invisibleRootItem()
            destination_parent = self.invisibleRootItem()
            destination_row = self.rowCount()

        # Restriction 1: No collection items cannot be moved to the root
        if source_item.data(Qt.ItemDataRole.UserRole).item_type != "Collection" and destination_item == self.invisibleRootItem():
            QMessageBox.warning(
                None, "Invalid Move", "Items cannot be moved to the root level."
            )
            return

        # Restriction 2: Avoid moving the item to the same row
        if source_parent == destination_parent and source_row == destination_row:
            return
        # Ensure that the destination row is valid
        if destination_row < 0 or destination_row > destination_parent.rowCount():
            # If the row is out of range, we avoid the operation.
            return

        # Restriction 3: Avoid moving an item to itself or to one of its descendants
        if destination_item == source_item:
            # Moving an item to itself
            return
        if destination_item.child(0) == source_item:
            # Moving an item to itself
            return

        self.layoutAboutToBeChanged.emit()

        # Remove the item from the source location
        source_row_data = source_parent.takeRow(source_row)

        if not source_row_data:
            # If the row is already empty, skip further processing
            self.layoutChanged.emit()
            return

        if destination_item and (destination_item.data(Qt.ItemDataRole.UserRole).item_type == "Collection"):
            if destination_row > destination_item.rowCount():
                destination_item.insertRow(destination_item.rowCount(), source_row_data)
            else:
                destination_item.insertRow(destination_row, source_row_data)
        elif destination_item == self.invisibleRootItem() and (source_item.data(Qt.ItemDataRole.UserRole).item_type == "Collection"):
            self.invisibleRootItem().appendRow(source_item)
        else:
            destination_parent.insertRow(destination_row, source_row_data)

        self.layoutChanged.emit()

        if destination_item != self.invisibleRootItem():
            self.signal_move_item.emit(destination_item)
        else:
            self.signal_move_item.emit(source_item)
