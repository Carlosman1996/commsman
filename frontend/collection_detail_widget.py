import sys

from PyQt6.QtCore import QModelIndex, QAbstractItemModel, Qt, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter, QTextEdit, QTableWidgetItem,
                             QTreeView, QSizePolicy)

from backend.backend_manager import BackendManager
from frontend.base_detail_widget import BaseDetail, BaseResult, BaseRequest
from frontend.common import convert_time, get_icon
from frontend.connection_tab_widget import ConnectionTabWidget
from frontend.history_tab_widget import HistoryTabWidget
from frontend.run_options_tab_widget import RunOptionsTabWidget


class CollectionRequestWidget(BaseRequest):

    CLIENT_TYPES = ["No connection", "Modbus TCP", "Modbus RTU"]

    def __init__(self, repository):
        super().__init__(repository)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        if self.item.parent_id:
            self.connection_widget = ConnectionTabWidget(repository, ["Inherit from parent"] + self.CLIENT_TYPES)
        else:
            self.connection_widget = ConnectionTabWidget(repository, self.CLIENT_TYPES)

        detail_tabs.addTab(self.connection_widget, "Connection")
        detail_tabs.addTab(RunOptionsTabWidget(repository), "Run options")

        main_layout.addWidget(detail_tabs)


class CollectionResultTreeView(QTreeView):
    def __init__(self):
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
        self.view_model = QStandardItemModel()
        self.view_model.setHorizontalHeaderLabels(["Name", "Status"])

        # Set the repository to the tree view
        self.setModel(self.view_model)

    def update_model(self, collection_results, collapse_view=False):
        # Clear the repository and repopulate it with updated data
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
        for child in collection_result.children:
            if child.item_handler == "CollectionResult":
                # Handle sub-collection
                self.populate_model(child, folder_item)
            else:
                # Handle request
                request_item = QStandardItem(child.name)
                text = self.get_request_status(child)
                status_item = QStandardItem(text)
                status_item.setIcon(get_icon(child.result))
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

    def __init__(self, backend):
        super().__init__(backend)

        self.repository = backend.repository

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
        self.results_tree = CollectionResultTreeView()
        self.results_layout.addWidget(self.results_tree)

        self.tabs.addTab(self.results_tab, "Results")

        # History
        self.history_tab = HistoryTabWidget(backend)
        self.tabs.addTab(self.history_tab, "History")

        # Set initial state and connect signals:
        self.update_view(load_data=True)

    def update_view(self, load_data=False, result=None):
        if not load_data:
            self.item.last_result = result
        if self.item.last_result is None:
            return

        self.results_tree.update_model(self.item.last_result, load_data)


class CollectionDetail(BaseDetail):
    def __init__(self, backend):
        super().__init__(backend)

        repository = backend.repository

        # Detail
        self.request_tabs = CollectionRequestWidget(repository)
        self.results_tabs = CollectionResultWidget(backend)

        # Fill splitter:
        self.request_layout.addWidget(self.request_tabs)
        self.result_layout.addWidget(self.results_tabs)
