import sys

from PyQt6.QtCore import QEvent, Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
    QTreeView,
    QHBoxLayout,
    QPushButton,
    QSizePolicy, QInputDialog, QMessageBox, QLineEdit, QDialog
)

from frontend.item_creation_dialog import ItemCreationDialog


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


class ProjectStructureSection(QWidget):
    def __init__(self):
        super().__init__()

        # Add button:
        self.add_button = Button("Add")
        self.add_button.clicked.connect(self.add_item)

        # Item creation dialog:
        self.item_creation_dialog = ItemCreationDialog()

        # Filter input:
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by name...")
        # self.filter_input.textChanged.connect(self.apply_filter)
        self.filter_input.textChanged.connect(self.apply_filter)

        # Tree view:
        self.tree_view = QTreeView()
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.viewport().installEventFilter(self)

        # Data model:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Project Structure"])

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
        if not selected_item:
            selected_item = self.model.invisibleRootItem()

        # Open the dialog
        dialog = ItemCreationDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print(f"Selected Item: {dialog.selected_item}")
            print(f"Entered Name: {dialog.item_name}")
            selected_item.appendRow(self._create_standard_item(dialog.item_name))
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
                model_index = self.proxy_model.mapToSource(selected_indexes[0])
                selected_item = self.model.itemFromIndex(model_index)
                parent_item = selected_item.parent() or self.model.invisibleRootItem()
                parent_item.removeRow(selected_item.row())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ProjectStructureSection()
    window.show()

    app.exec()
