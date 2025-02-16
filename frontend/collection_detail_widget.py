import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QTabWidget, QHBoxLayout, QSplitter)

from frontend.base_detail_widget import BaseDetail
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

        # Set initial state:
        self.update_view()

    def update_view(self):
        self.connection_widget.error_label.setVisible(False)


class CollectionDetail(BaseDetail):
    def __init__(self, model, controller):
        super().__init__(model, controller)

        # Detail
        self.detail_tabs = CollectionRequestWidget(model, controller)

        # Fill splitter:
        self.splitter.addWidget(self.detail_tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(Collection(name="Collection Test"))
    window = CollectionDetail(model)
    window.show()
    sys.exit(app.exec())