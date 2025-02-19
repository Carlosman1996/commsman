import sys

from PyQt6.QtCore import QModelIndex, QAbstractItemModel, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter, QTextEdit, QTableWidgetItem,
                             QTreeView, QSizePolicy)

from backend.backend_manager import BackendManager
from frontend.base_detail_widget import BaseDetail
from frontend.components.components import CustomTable
from frontend.connection_tab_widget import ConnectionTabWidget
from frontend.model import Model
from frontend.models.collection import Collection
from frontend.run_options_tab_widget import RunOptionsTabWidget


class CollectionRequestWidget(QWidget):

    CLIENT_TYPES = ["No connection", "Modbus TCP", "Modbus RTU"]

    def __init__(self, model, controller):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        item = model.get_selected_item()
        if hasattr(item, "parent") and (item.parent()):
            self.connection_widget = ConnectionTabWidget(model, controller, ["Inherit from parent"] + self.CLIENT_TYPES)
        else:
            self.connection_widget = ConnectionTabWidget(model, controller, self.CLIENT_TYPES)

        detail_tabs.addTab(self.connection_widget, "Connection")
        detail_tabs.addTab(RunOptionsTabWidget(model), "Run options")

        main_layout.addWidget(detail_tabs)


class CollectionResultTreeView(QTreeView):
    def __init__(self, collection_results):
        super().__init__()

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
        self.tree_view = QTreeView(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name', 'Status'])

        # Populate the model with data
        self.populate_model(self.model, collection_results)

        # Set the model to the tree view
        self.tree_view.setModel(self.model)

    def populate_model(self, model, collection_result, parent=None):
        # Create a folder item for the collection
        folder_item = QStandardItem(f"{collection_result.name}")
        status_item = QStandardItem(self.get_collection_status(collection_result))

        if parent is None:
            model.appendRow([folder_item, status_item])
        else:
            parent.appendRow([folder_item, status_item])

        # Add sub-collections
        for sub_collection in collection_result.collections:
            self.populate_model(model, sub_collection, folder_item)

        # Add requests
        for request in collection_result.requests:
            request_item = QStandardItem(request.name)
            status_item = QStandardItem(self.get_request_status(request))
            folder_item.appendRow([request_item, status_item])

    def get_collection_status(self, collection_result):
        total_requests = collection_result.total_ok + collection_result.total_failed + collection_result.total_pending
        if collection_result.total_failed > 0:
            return f"Failed ({total_requests} requests: {collection_result.total_ok} OK, {collection_result.total_failed} Failed)"
        else:
            return f"Success ({total_requests} requests: {collection_result.total_ok} OK)"

    def get_request_status(self, request):
        if request.result == "Passed":
            return "OK  ✅"
        else:
            return f"❌ ({request.error_message})"


class CollectionResultWidget(QWidget):

    def __init__(self, model, controller):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Response Tab
        self.results_tab = None

        # Set initial state and connect signals:
        self.update_view()

        controller.signal_request_finished.connect(self.update_view)

    def update_view(self):
        self.results_tab = CollectionResultTreeView(self.item.last_response)
        self.tabs.addTab(self.results_tab, "Results")

    def update_view_table(self):
        response = self.item.last_response
        if response is None:
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

        set_collection_items(self.item.last_response)

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
        self.splitter.addWidget(self.request_tabs)
        self.splitter.addWidget(self.results_tabs)

        # Connect signals and slots
        self.set_results()
        controller.signal_request_finished.connect(self.set_results)

    def set_results(self):
        if self.item.last_response:
            self.results_tabs.setVisible(True)
        else:
            self.results_tabs.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(Collection(name="Collection Test"))
    controller = BackendManager(model)
    window = CollectionDetail(model, controller)
    window.show()
    sys.exit(app.exec())
