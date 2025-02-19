import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter, QTextEdit, QTableWidgetItem)

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
        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_tab.setLayout(self.results_layout)

        # Response values table (initially hidden)
        self.values_table = CustomTable(["Parent", "Type", "Name", "Result", "Timestamp"])
        self.results_layout.addWidget(self.values_table)

        self.results_layout.addStretch()

        self.tabs.addTab(self.results_tab, "Results")

        # Set initial state and connect signals:

        self.update_view()

        controller.signal_request_finished.connect(self.update_view)

    def update_view(self):
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
