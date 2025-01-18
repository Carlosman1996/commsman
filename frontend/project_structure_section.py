import json
import os
import pickle
import sys

from PyQt6.QtCore import QEvent, Qt, QSortFilterProxyModel, QRect, pyqtSignal, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
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
    QStyle
)

from frontend.common import ITEMS
from frontend.item_creation_dialog import ItemCreationDialog
from utils.common import PROJECT_PATH, FRONTEND_PATH, OUTPUTS_PATH


TREE_DATA_FILE = os.path.join(PROJECT_PATH, "project_structure_data.pkl")


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy()
        self.setSizePolicy(size_policy)
        self.adjustSize()


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


class CustomTreeItem(QStandardItem):

    def __init__(self, name, type="Collection"):
        super().__init__(name)

        self.name = name
        self.type = type
        self.setIcon(QIcon(ITEMS[type]["icon_simple"]))
        self.setEditable(True)


class CustomItemDelegate(QStyledItemDelegate):

    # Define signals for export and delete
    signal_delete_clicked = pyqtSignal(QModelIndex)
    signal_export_clicked = pyqtSignal(QModelIndex)

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

        if not index.parent().isValid():
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

            if QRect(delete_x, rect.top(), icon_size, icon_size).contains(click_pos):
                # Handle delete action
                self.signal_delete_clicked.emit(index)
                return True

            elif QRect(export_x, rect.top(), icon_size, icon_size).contains(click_pos):
                # Handle export action
                self.signal_export_clicked.emit(index)
                return True

        return False


class ProjectStructureSection(QWidget):
    def __init__(self):
        super().__init__()

        # Buttons:
        self.add_button = Button("Add")
        self.add_button.clicked.connect(self.add_item)

        # Filter input:
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by name...")
        # self.filter_input.textChanged.connect(self.apply_filter)
        self.filter_input.textChanged.connect(self.apply_filter)

        # Tree view:
        self.tree_view = QTreeView()
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.viewport().installEventFilter(self)

        # Attach custom delegate
        self.delegate = CustomItemDelegate(self.tree_view)
        self.tree_view.setItemDelegate(self.delegate)
        self.delegate.signal_delete_clicked.connect(self.delete_selected_item)
        self.delegate.signal_export_clicked.connect(self.export_selected_item)

        # Data model:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Project Structure"])
        self.model.itemChanged.connect(self.edit_item)

        # Proxy model to filter tree:
        self.proxy_model = HierarchicalFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
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

        # Load data model:
        self.load_tree_data()

    def eventFilter(self, source, event):
        if source == self.tree_view.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            clicked_index = self.tree_view.indexAt(event.pos())
            if not clicked_index.isValid():
                self.tree_view.clearSelection()
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        super().keyPressEvent(event)

    def apply_filter(self, text):
        self.proxy_model.setFilterRegularExpression(text)
        self.tree_view.expandAll()

    def get_selected_item(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            model_index = self.proxy_model.mapToSource(selected_indexes[0])
            return self.model.itemFromIndex(model_index)
        return None

    def _instantiate_item(self, name, type):
        item = CustomTreeItem(name, type)
        return item

    def add_item(self):
        selected_item = self.get_selected_item()
        dialog = ItemCreationDialog(selected_item)
        if not selected_item:
            selected_item = self.model.invisibleRootItem()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_item = self._instantiate_item(dialog.item_name, dialog.item_type)
            selected_item.appendRow(new_item)

            self.tree_view.expandAll()
            self.autosave_tree_data()

    def edit_item(self, item):
        item.name = item.text()
        self.autosave_tree_data()

    def get_item_from_index(self, index):
        model_index = self.proxy_model.mapToSource(index)
        return self.model.itemFromIndex(model_index)

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
                selected_item = self.get_item_from_index(indexes[0])
                parent_item = selected_item.parent() or self.model.invisibleRootItem()
                parent_item.removeRow(selected_item.row())
                self.autosave_tree_data()

    def export_selected_item(self, index):
        item = self.get_item_from_index(index)

        reply = QMessageBox.question(
            None, "Export Confirmation",
            f"Do you want to export '{item.name}' and its children to JSON?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            def serialize(item):
                return {
                    "name": item.name,
                    "type": item.type,
                    "children": [serialize(item.child(row)) for row in range(item.rowCount())],
                }

            data = serialize(item)
            file_path = f"{OUTPUTS_PATH}/{item.name}.json"
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            QMessageBox.information(None, "Export Successful", f"Data exported to {file_path}")

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
                "name": getattr(item, "name", item.text()),
                "type": getattr(item, "type", "Collection"),
                "children": [serialize_item(item.child(i)) for i in range(item.rowCount())],
            }

        root_item = self.model.invisibleRootItem()
        return [serialize_item(root_item.child(i)) for i in range(root_item.rowCount())]

    def deserialize_tree(self, data):
        def deserialize_item(data, parent):
            item = self._instantiate_item(data["name"], data["type"])

            parent.appendRow(item)
            for child_data in data["children"]:
                deserialize_item(child_data, item)

        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Items"])
        for item_data in data:
            deserialize_item(item_data, self.model.invisibleRootItem())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ProjectStructureSection()
    window.show()

    app.exec()
