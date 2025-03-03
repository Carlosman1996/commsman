import sys

from PyQt6.QtCore import QModelIndex, QAbstractItemModel, Qt, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter, QTextEdit, QTableWidgetItem,
                             QTreeView, QSizePolicy)

from backend.backend_manager import BackendManager
from frontend.base_detail_widget import BaseDetail, BaseResult, BaseRequest
from frontend.common import convert_time
from frontend.connection_tab_widget import ConnectionTabWidget
from frontend.run_options_tab_widget import RunOptionsTabWidget


class CollectionRequestWidget(BaseRequest):

    CLIENT_TYPES = ["No connection", "Modbus TCP", "Modbus RTU"]

    def __init__(self, model, controller):
        super().__init__(model)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        item = model.get_selected_item()
        if hasattr(item, "parent") and item.parent:
            self.connection_widget = ConnectionTabWidget(model, controller, ["Inherit from parent"] + self.CLIENT_TYPES)
        else:
            self.connection_widget = ConnectionTabWidget(model, controller, self.CLIENT_TYPES)

        detail_tabs.addTab(self.connection_widget, "Connection")
        detail_tabs.addTab(RunOptionsTabWidget(model), "Run options")

        main_layout.addWidget(detail_tabs)


class CollectionResultTreeView(QTreeView):
    def __init__(self, model):
        super().__init__()

        self.model = model

        self.setStyleSheet("""
            QTreeView::item:selected {
                background-color: #C89BD2;  /* Optional: Set a selection background color */
            }
            QTreeView::branch {
                margin-left: -5px;  /* Pull branch indicators closer to items */
                border-image: none;
            }
        """)

        # Create a QTreeView and a QStandardItemModel
        self.view_model = QStandardItemModel()
        self.view_model.setHorizontalHeaderLabels(["Name", "Status"])

        # Set the model to the tree view
        self.setModel(self.view_model)

    def update_model(self, collection_results, collapse_view=False):
        # Clear the model and repopulate it with updated data
        self.view_model.clear()
        self.view_model.setHorizontalHeaderLabels(["Name", "Status"])

        self.setColumnWidth(0, 200)  # Minimum width for column 0
        self.setColumnWidth(1, 200)  # Minimum width for column 1

        self.populate_model(collection_results)

        if not collapse_view:
            # Expand all items in the tree view
            self.expandAll()
        else:
            first_index = self.view_model.index(0, 0)
            self.expand(first_index)

    def populate_model(self, collection_result, parent=None):
        """Populate the QStandardItemModel with collections and requests."""
        # Create a folder item for the collection
        folder_item = QStandardItem(f"{collection_result.name}")
        status_item = QStandardItem(self.get_collection_status(collection_result))

        if parent is None:
            self.view_model.appendRow([folder_item, status_item])
        else:
            parent.appendRow([folder_item, status_item])

        # Iterate through children (both collections and requests)
        for child_uuid in collection_result.children:
            child = self.model.get_item(child_uuid)

            if child.item_type == "Collection":
                # Handle sub-collection
                self.populate_model(child, folder_item)
            else:
                # Handle request
                request_item = QStandardItem(child.name)
                text = self.get_request_status(child)
                status_item = QStandardItem(text)
                if child.result == "Pending":
                    status_item.setIcon(QIcon.fromTheme("go-next"))  # Green check icon
                elif child.result == "OK":
                    status_item.setIcon(QIcon.fromTheme("dialog-ok"))  # Green check icon
                else:
                    status_item.setIcon(QIcon.fromTheme("dialog-error"))  # Red X icon
                folder_item.appendRow([request_item, status_item])

    def get_collection_status(self, collection_result):
        total_requests = collection_result.total_ok + collection_result.total_failed + collection_result.total_pending
        if collection_result.total_failed > 0:
            return f"Failed ({total_requests} requests: {collection_result.total_ok} OK, {collection_result.total_failed} Failed)"
        else:
            return f"Success ({total_requests} requests: {collection_result.total_ok} OK)"

    def get_request_status(self, request):
        if request.result == "Pending":
            return f"Pending"
        elif request.result == "OK":
            return f"OK  [ {convert_time(request.elapsed_time)} ]"
        else:
            return f"Failed  [ {convert_time(request.elapsed_time)} ]"


class CollectionResultWidget(BaseResult):

    def __init__(self, model, controller):
        super().__init__(model, controller)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Results Tab
        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_tab.setLayout(self.results_layout)

        # Tree view in results tab
        self.results_tree = CollectionResultTreeView(self.model)
        self.results_layout.addWidget(self.results_tree)

        self.tabs.addTab(self.results_tab, "Results")

        # Set initial state and connect signals:
        self.update_view(load_data=True)

    def update_view(self, load_data=False):
        result = self.item.last_result
        if result is None:
            return

        self.results_tree.update_model(result, load_data)

    def update_view_table(self):
        result = self.item.last_result
        if result is None:
            return

        table_values = []

        def add_row(item):
            table_values.append([])

            item_parent = QTableWidgetItem(str(item.parent))
            table_values[-1].append(item_parent)
            item_type = QTableWidgetItem(str(item.item_type))
            table_values[-1].append(item_type)
            item_name = QTableWidgetItem(str(item.name))
            table_values[-1].append(item_name)
            item_result = QTableWidgetItem(str(item.result))
            table_values[-1].append(item_result)
            item_timestamp = QTableWidgetItem(str(item.timestamp))
            table_values[-1].append(item_timestamp)

        def set_collection_items(collection):
            for request in collection.requests:
                add_row(request)
            for subcollection in collection.collections:
                add_row(subcollection)
                set_collection_items(subcollection)

        set_collection_items(self.item.last_result)

        self.values_table.clear()
        self.values_table.setRowCount(len(table_values))
        for index_row, row in enumerate(table_values):
            for index_column, item in enumerate(row):
                self.values_table.setItem(index_row, index_column, item)


class CollectionDetail(BaseDetail):
    def __init__(self, model, controller):
        super().__init__(model, controller)

        # Detail
        self.request_tabs = CollectionRequestWidget(model, controller)
        self.results_tabs = CollectionResultWidget(model, controller)

        # Fill splitter:
        self.request_layout.addWidget(self.request_tabs)
        self.result_layout.addWidget(self.results_tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(Collection(name="Collection Test"))
    controller = BackendManager(model)
    window = CollectionDetail(model, controller)
    window.show()
    sys.exit(app.exec())
