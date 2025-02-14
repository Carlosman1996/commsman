import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter)

from frontend.base_detail_widget import BaseDetail
from frontend.components.components import CustomGridLayout, CustomTable, IconTextWidget, CustomComboBox
from frontend.connection_tab_widget import ConnectionTabWidget
from frontend.model import Model
from frontend.models.collection import Collection
from frontend.common import ITEMS


class CollectionRequestWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        connection_widget = ConnectionTabWidget(model, ["No connection", "Modbus TCP", "Modbus RTU"])
        detail_tabs.addTab(connection_widget, "Connection")

        main_layout.addWidget(detail_tabs)


class CollectionDetail(BaseDetail):
    def __init__(self, model):
        super().__init__(model)

        # Detail
        self.detail_tabs = CollectionRequestWidget(model)

        # Fill splitter:
        self.splitter.addWidget(self.detail_tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(Collection(name="Collection Test"))
    window = CollectionDetail(model)
    window.show()
    sys.exit(app.exec())