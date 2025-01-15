import sys

from PyQt6.QtCore import QEvent, Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
from PyQt6.QtWidgets import (
    QLabel,
    QApplication,
    QVBoxLayout,
    QWidget,
    QTreeView,
    QHBoxLayout,
    QPushButton,
    QSizePolicy, QInputDialog, QMenu, QAbstractItemView, QMessageBox, QLineEdit
)


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy()
        self.setSizePolicy(size_policy)
        self.adjustSize()


class ProjectStructureSection(QWidget):
    def __init__(self):
        super().__init__()

        # Add button:
        self.add_button = Button("Add")
        self.add_button.clicked.connect(self.add_item)

        # Filter input:
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by name...")
        self.filter_input.textChanged.connect(self.apply_filter)

        # Tree model and view:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Project Structure"])
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.viewport().installEventFilter(self)

        # Proxy model to filter tree:
        self.proxy_model = QSortFilterProxyModel(self)
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
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        super().keyPressEvent(event)

    def apply_filter(self):
        filter_text = self.filter_input.text()
        self.proxy_model.setFilterFixedString(filter_text)

    def get_selected_item(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            return self.model.itemFromIndex(selected_indexes[0])
        return None

    def add_item(self):
        selected_item = self.get_selected_item()
        if not selected_item:
            selected_item = self.model.invisibleRootItem()

        item_name, ok = QInputDialog.getText(self, "Add Item", "Enter name:")
        if ok and item_name.strip():
            selected_item.appendRow(self._create_standard_item(item_name))
        self.tree_view.expandAll()

    def _create_standard_item(self, name: str):
        item = QStandardItem(name)
        # item.setIcon(QIcon("icon_path.png"))  # TODO: Asignar un ícono
        return item

    def delete_selected_item(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if len(selected_indexes) == 1:
            reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this item?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:

                selected_item = self.model.itemFromIndex(selected_indexes[0])
                parent_item = selected_item.parent() or self.model.invisibleRootItem()
                parent_item.removeRow(selected_item.row())

    def edit_item(self):
        selected_item = self.get_selected_item()
        if selected_item:
            new_name, ok = QInputDialog.getText(self, "Edit Item", "Enter new name:", text=selected_item.text())
            if ok and new_name.strip():
                selected_item.setText(new_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ProjectStructureSection()
    window.show()

    app.exec()
