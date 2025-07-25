import dataclasses
import json
import sys

from PyQt6.QtCore import QEvent, Qt, QSortFilterProxyModel, QRect, pyqtSignal, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QIcon, QDrag, QMouseEvent, QStandardItem
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
    QTreeView,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QLineEdit,
    QDialog,
    QStyledItemDelegate,
    QStyle,
)

from backend.core.backend_manager import BackendManager
from frontend.api.api_helper_mixin import ApiCallMixin
from frontend.common import ITEMS
from frontend.item_creation_dialog import ItemCreationDialog
from config import FRONTEND_PATH, OUTPUTS_PATH
from frontend.safe_base import SafeWidget


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy()
        self.setSizePolicy(size_policy)
        self.adjustSize()


class CustomStandardItem(QStandardItem):
    def __init__(self, item_name, item_handler):
        super().__init__(item_name)

        self.setIcon(QIcon(ITEMS[item_handler]["icon_simple"]))
        self.setEditable(True)


class CustomStandardItemModel(QStandardItemModel, ApiCallMixin):

    signal_move_item = pyqtSignal(CustomStandardItem)
    signal_update_item = pyqtSignal()

    def __init__(self, api_client, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setup_api_client(api_client)

        self.view_items = {}

        # Load all model by calling the API:
        self.call_api(api_method="get_items_request_tree",
                      callback=self.load_model)

    def create_view_item(self, item) -> CustomStandardItem:
        view_item = CustomStandardItem(item["name"], item["item_handler"])
        item_data = {
            "item_id": item["item_id"],
            "item_handler": item["item_handler"],
        }
        view_item.setData(item_data, role=Qt.ItemDataRole.UserRole)
        self.view_items[item["item_id"]] = view_item  # Save reference
        return view_item

    def load_model(self, data: dict):
        """Loads all elements from repository into a QStandardItemModel, considering the 'position' key."""
        self.view_items = {}
        self.clear()
        self.setHorizontalHeaderLabels(["Project"])

        # Step 1: Create QStandardItem objects for each item
        def get_items(data):
            if not data:
                return
            for db_item in data:
                item = self.create_view_item(db_item)
                self.view_items[db_item.get("item_id")] = item
                get_items(db_item.get("children"))
        # Get items::
        get_items(data)

        # Step 2: Attach items to parents, maintaining order
        root_level_item = self.invisibleRootItem()
        def set_model(data):
            if not data:
                return
            for db_item in data:
                if db_item.get("parent_id"):  # Attach to a parent
                    parent_view_item = self.view_items.get(db_item.get("parent_id"))
                    parent_view_item.appendRow(self.view_items[db_item.get("item_id")])
                else:  # Root-level items
                    root_level_item.appendRow(self.view_items[db_item.get("item_id")])
                set_model(db_item.get("children"))
        # Set model:
        set_model(data)

    def recalculate_positions(self):
        """Recalculates and updates the 'position' of each item based on its order in the QStandardItemModel."""

        def update_positions_recursive(parent_item):
            """Recursively updates positions of child items under the given parent."""
            for index in range(parent_item.rowCount()):
                child_item = parent_item.child(index)
                item_data = child_item.data(Qt.ItemDataRole.UserRole)  # Retrieve the unique identifier

                # Update position based on index within the parent
                self.call_api(api_method="update_item_from_handler",
                              item_handler=item_data["item_handler"],
                              item_id=item_data["item_id"],
                              position=index)

                # Recursively update children
                update_positions_recursive(child_item)

        root_item = self.invisibleRootItem()
        update_positions_recursive(root_item)

    def move_to_destination(self, source_index, destination_index):
        """Move an item to the exact drop location with restrictions."""
        if not source_index.isValid():
            return

        source_item = self.itemFromIndex(source_index)
        item_data = source_item.data(Qt.ItemDataRole.UserRole)
        source_parent = source_item.parent() or self.invisibleRootItem()
        source_row = source_item.row()

        if destination_index.isValid():
            destination_item = self.itemFromIndex(destination_index)
            destination_parent = destination_item.parent() or self.invisibleRootItem()
            destination_row = destination_index.row()
            destination_data = destination_item.data(Qt.ItemDataRole.UserRole)
        else:
            # Dropping to the root
            destination_item = self.invisibleRootItem()
            destination_parent = self.invisibleRootItem()
            destination_row = self.rowCount()
            destination_data = None

        # Restriction 1: No collection items cannot be moved to the root
        if item_data["item_handler"] != "Collection" and destination_item == self.invisibleRootItem():
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

        if destination_item != self.invisibleRootItem() and (destination_data.get("item_handler") == "Collection"):
            if destination_parent != source_parent:
                destination_item.insertRow(0, source_row_data)
            elif destination_row > destination_item.rowCount():
                destination_item.insertRow(destination_item.rowCount(), source_row_data)
            else:
                destination_item.insertRow(destination_row, source_row_data)
            parent_data = destination_data
        elif destination_item == self.invisibleRootItem() and (item_data["item_handler"] == "Collection"):
            self.invisibleRootItem().appendRow(source_item)
            parent_data = {}
        else:
            destination_parent.insertRow(destination_row, source_row_data)
            parent_item = destination_item.parent()
            parent_data = parent_item.data(Qt.ItemDataRole.UserRole)

        self.layoutChanged.emit()

        # Update backend repository
        self.call_api(api_method="update_item_from_handler",
                      item_handler=item_data["item_handler"],
                      item_id=item_data["item_id"],
                      parent_id=parent_data.get("item_id"))

        if destination_item != self.invisibleRootItem():
            self.signal_move_item.emit(destination_item)
        else:
            self.signal_move_item.emit(source_item)

        self.recalculate_positions()

    def add_item(self, item):
        view_item = self.create_view_item(item)
        root_level_item = self.invisibleRootItem()
        if item["parent_id"]:
            self.view_items[item["parent_id"]].appendRow(view_item)
        else:
            root_level_item.appendRow(view_item)

        self.recalculate_positions()

    def delete_item(self, item_id: int):
        view_item = self.view_items[item_id]
        root_level_item = self.invisibleRootItem()
        parent_item = view_item.parent() or root_level_item
        parent_item.removeRow(view_item.row())
        self.view_items.pop(item_id)  # Delete reference

        self.recalculate_positions()


class HierarchicalFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        # Get the source index for the current row:
        source_index = self.sourceModel().index(source_row, 0, source_parent)

        # Check if the current row matches the filter:
        if self.filterRegularExpression().match(self.sourceModel().data(source_index)).hasMatch():
            return True

        # Recursively check if any child matches the filter:
        for row in range(self.sourceModel().rowCount(source_index)):
            if self.filterAcceptsRow(row, source_index):
                return True

        # If neither the current row nor its children match, filter out the row:
        return False


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewport().installEventFilter(self)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)

        self.setStyleSheet("""
            QTreeView::item:selected {
                background-color: #C89BD2;  /* Optional: Set a selection background color */
            }
            QTreeView::branch {
                margin-left: -5px;  /* Pull branch indicators closer to items */
                border-image: none;
            }
        """)

    def startDrag(self, supportedActions):
        """Start drag operation."""
        index = self.currentIndex()
        if not index.isValid():
            return

        mime_data = self.model().mimeData([index])
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(supportedActions)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move event."""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            super().dragMoveEvent(event)
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle the drop event."""
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.ignore()
            return

        source_index = self.currentIndex()
        destination_index = self.indexAt(event.position().toPoint())

        proxy_model = self.model()
        source_model_index = proxy_model.mapToSource(source_index)
        destination_model_index = proxy_model.mapToSource(destination_index)

        # Move the item in the source repository
        proxy_model.sourceModel().move_to_destination(source_model_index, destination_model_index)

        event.accept()

        self.viewport().update()  # Redraw the view

    def mousePressEvent(self, event: QMouseEvent):
        # Call the base class implementation
        super().mousePressEvent(event)

        # Check if the clicked position corresponds to a valid item
        index = self.indexAt(event.pos())
        if not index.isValid():
            # Clear the selection if the click is outside any item
            self.clearSelection()


class CustomItemDelegate(QStyledItemDelegate):

    # Define signals for export and delete
    signal_delete_clicked = pyqtSignal(QModelIndex)
    signal_export_clicked = pyqtSignal(QModelIndex)
    signal_item_clicked = pyqtSignal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.export_icon = QIcon(f"{FRONTEND_PATH}/icons/export.png")
        self.delete_icon = QIcon(f"{FRONTEND_PATH}/icons/delete.png")

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        rect = option.rect
        icon_size = 16
        spacing = 5

        # Calculate positions for the icons
        delete_x = rect.right() - icon_size - spacing
        export_x = delete_x - icon_size - spacing

        # Only show the export icon if the item is selected, and it is root collection:
        if not index.parent().isValid() and (option.state & QStyle.StateFlag.State_Selected):
            self.export_icon.paint(painter, QRect(export_x, rect.top() + (rect.height() - icon_size) // 2, icon_size, icon_size))

        # Only show the delete icon if the item is selected
        if option.state & QStyle.StateFlag.State_Selected:
            self.delete_icon.paint(painter, QRect(delete_x, rect.top() + (rect.height() - icon_size) // 2, icon_size, icon_size))

    def editorEvent(self, event, model, option, index):
        """Handle mouse clicks on export and delete icons."""
        if event.type() == QEvent.Type.MouseButtonRelease:
            rect = option.rect
            icon_size = 16
            spacing = 5

            delete_x = rect.right() - icon_size - spacing
            export_x = delete_x - icon_size - spacing

            # Determine if the click was on the delete or export icon
            click_pos = event.pos()

            self.signal_item_clicked.emit(index)

            if QRect(delete_x, rect.top() + (rect.height() - icon_size) // 2, icon_size, icon_size).contains(click_pos):
                # Handle delete action
                self.signal_delete_clicked.emit(index)
                return True

            if not index.parent().isValid() and QRect(export_x, rect.top() + (rect.height() - icon_size) // 2, icon_size, icon_size).contains(click_pos):
                # Handle export action
                self.signal_export_clicked.emit(index)
                return True

        return False


class ProjectStructureSection(SafeWidget, ApiCallMixin):
    def __init__(self, api_client):
        super().__init__()

        self.setMinimumWidth(250)

        # Set api client:
        self.setup_api_client(api_client)

        # Buttons:
        self.add_button = Button("Add")
        self.add_button.clicked.connect(self.create_item)
        self.add_button.setFixedHeight(40)

        # Filter input:
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by name...")
        self.filter_input.textChanged.connect(self.apply_filter)
        self.filter_input.setFixedHeight(40)

        # Tree view:
        self.tree_view = CustomTreeView()

        # Attach custom delegate
        self.delegate = CustomItemDelegate(self.tree_view)
        self.tree_view.setItemDelegate(self.delegate)
        self.delegate.signal_delete_clicked.connect(self.delete_selected_item)
        self.delegate.signal_export_clicked.connect(self.export_selected_item)
        self.delegate.signal_item_clicked.connect(self.set_add_button_visibility)

        # Data repository:
        self.view_model = CustomStandardItemModel(self.api_client)
        self.view_model.itemChanged.connect(self.edit_item)
        self.view_model.signal_move_item.connect(self.move_item)

        # Proxy repository to filter tree:
        self.proxy_model = HierarchicalFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.view_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.tree_view.setModel(self.proxy_model)

        # Set filters layout:
        subsection_layout = QHBoxLayout()
        subsection_layout.addWidget(self.filter_input)
        subsection_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Set complete layout:
        section_layout = QVBoxLayout()
        section_layout.addLayout(subsection_layout)
        section_layout.addWidget(self.tree_view)

        self.setLayout(section_layout)

    def eventFilter(self, source, event):
        if source == self.tree_view.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            clicked_index = self.tree_view.indexAt(event.pos())
            if not clicked_index.isValid():
                self.tree_view.clearSelection()
                self.add_button.show()
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        super().keyPressEvent(event)

    def apply_filter(self, text):
        self.proxy_model.setFilterRegularExpression(text)
        self.tree_view.expandAll()

    def expand_tree_view_item(self, item):
        def expand_all_parents(index):
            while index.isValid():
                self.tree_view.expand(index)
                index = index.parent()

        item_index = self.view_model.indexFromItem(item)
        item_proxy_model_index = self.proxy_model.mapFromSource(item_index)
        expand_all_parents(item_proxy_model_index)

    def get_selected_item(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            model_index = self.proxy_model.mapToSource(selected_indexes[0])
            return self.view_model.itemFromIndex(model_index)
        return None

    def get_selected_item_data(self) -> int | None:
        item = self.get_selected_item()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)["item_id"]
        return None

    def get_item_from_selected_index(self, index):
        model_index = self.proxy_model.mapToSource(index)
        return self.view_model.itemFromIndex(model_index)

    def create_item(self, *args, **kwargs):
        selected_item = self.get_selected_item()
        dialog = ItemCreationDialog(selected_item)
        if not selected_item:
            selected_item = self.view_model.invisibleRootItem()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if selected_item and selected_item != self.view_model.invisibleRootItem():
                parent_data = selected_item.data(Qt.ItemDataRole.UserRole)
            else:
                parent_data = {}

            self.call_api(api_method="create_item_request_from_handler",
                          item_name=dialog.item_name,
                          item_handler=dialog.item_handler,
                          parent_item_id=parent_data.get("item_id"),
                          callback=self.view_model.add_item)

            self.expand_tree_view_item(selected_item)

    def set_add_button_visibility(self, *args, **kwargs):
        selected_item = self.get_selected_item()
        item_data = selected_item.data(Qt.ItemDataRole.UserRole)
        if item_data["item_handler"] == "Collection":
            self.add_button.show()
        else:
            self.add_button.hide()

    def edit_item(self, item):
        item_data = item.data(Qt.ItemDataRole.UserRole)
        self.call_api(api_method="update_item_from_handler",
                      item_handler=item_data["item_handler"],
                      item_id=item_data["item_id"],
                      name=item.text())

    def move_item(self, item, *args, **kwargs):
        self.proxy_model.setSourceModel(None)
        self.proxy_model.setSourceModel(self.view_model)
        self.expand_tree_view_item(item)

    def delete_selected_item(self, index = None):
        # Click delete icon:
        if index:
            indexes = [index]
        # Press 'SUPR' button:
        else:
            indexes = self.tree_view.selectedIndexes()

        if len(indexes) == 1:
            reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this item?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                selected_item = self.get_item_from_selected_index(indexes[0])
                item_data = selected_item.data(Qt.ItemDataRole.UserRole)
                self.call_api(api_method="delete_item",
                              item_id=item_data["item_id"])
                self.view_model.delete_item(item_id=item_data["item_id"])
                self.set_add_button_visibility()

    def export_selected_item(self, index, *args, **kwargs):
        item = self.get_item_from_selected_index(index)

        reply = QMessageBox.question(
            None, "Export Confirmation",
            f"Do you want to export '{item.text()}' and its children to JSON?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            def serialize(item):
                return {
                    "data": dataclasses.asdict(item),
                    "children": [serialize(item.child(row)) for row in range(item.rowCount())],
                }

            data = serialize(item)
            file_path = f"{OUTPUTS_PATH}/{item.text()}.json"
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            QMessageBox.information(None, "Export Successful", f"Data exported to {file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    backend = BackendManager()
    window = ProjectStructureSection(backend.repository)
    window.show()

    app.exec()
