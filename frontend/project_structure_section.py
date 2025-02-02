import dataclasses
import json
import os
import sys

from PyQt6.QtCore import QEvent, Qt, QSortFilterProxyModel, QRect, pyqtSignal, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QIcon, QDrag
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

from frontend.item_creation_dialog import ItemCreationDialog
from frontend.model import CustomStandardItem, Item
from utils.common import FRONTEND_PATH, OUTPUTS_PATH


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
                background-color: #F78434;  /* Optional: Set a selection background color */
            }
            QTreeView::branch {
                margin-left: -5px;  /* Pull branch indicators closer to items */
                border-image: none;
            }
        """)
        # self.setIndentation(40)

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

        # Move the item in the source model
        proxy_model.sourceModel().move_to_destination(source_model_index, destination_model_index)

        event.accept()

        self.viewport().update()  # Redraw the view


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


class ProjectStructureSection(QWidget):
    def __init__(self, model=None):
        super().__init__()

        self.setMinimumWidth(400)

        # Buttons:
        self.add_button = Button("Add")
        self.add_button.clicked.connect(self.add_item)
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

        # Data model:
        self.model = model
        self.model.itemChanged.connect(self.edit_item)
        self.model.signal_move_item.connect(self.move_item)

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

    def get_selected_item(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            model_index = self.proxy_model.mapToSource(selected_indexes[0])
            return self.model.itemFromIndex(model_index)
        return None

    def add_item(self):
        selected_item = self.get_selected_item()
        dialog = ItemCreationDialog(selected_item)
        if not selected_item:
            selected_item = self.model.invisibleRootItem()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_item_data = Item(dialog.item_name, dialog.item_type)
            new_item = CustomStandardItem(new_item_data.dataclass)
            selected_item.appendRow(new_item)

            self.tree_view.expandAll()
            self.model.autosave_tree_data()

    def set_add_button_visibility(self):
        selected_item = self.get_selected_item()
        if selected_item.data(Qt.ItemDataRole.UserRole).item_type == "Collection":
            self.add_button.show()
        else:
            self.add_button.hide()

    def edit_item(self, item):
        item.data(Qt.ItemDataRole.UserRole).name = item.text()
        self.model.autosave_tree_data()

    def move_item(self, item):
        def expand_all_parents(index):
            while index.isValid():
                self.tree_view.expand(index)
                index = index.parent()

        self.proxy_model.setSourceModel(None)
        self.proxy_model.setSourceModel(self.model)

        item_index = self.model.indexFromItem(item)
        item_proxy_model_index = self.proxy_model.mapFromSource(item_index)
        expand_all_parents(item_proxy_model_index)

        self.model.autosave_tree_data()

    def get_item_from_selected_index(self, index):
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
                selected_item = self.get_item_from_selected_index(indexes[0])
                parent_item = selected_item.parent() or self.model.invisibleRootItem()
                parent_item.removeRow(selected_item.row())
                self.model.autosave_tree_data()

    def export_selected_item(self, index):
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

    window = ProjectStructureSection()
    window.show()

    app.exec()
