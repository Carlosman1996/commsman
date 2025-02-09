import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout,
                             QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QTableWidgetItem, QSplitter)

from backend.modbus_handler import ModbusHandler, convert_value_after_sending
from frontend.components.components import CustomGridLayout, CustomTable, IconTextWidget, CustomComboBox
from frontend.model import Model
from frontend.models.collection import Collection
from frontend.models.modbus import ModbusRequest, ModbusClient, ModbusResponse
from frontend.common import ITEMS



class CollectionConnectionTabWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        self.grid_layout = QVBoxLayout()

        self.connection_type_combo = CustomComboBox()
        self.connection_type_combo.addItems(["No connection", "Modbus TCP", "Modbus RTU"])
        if self.item.connection_client:
            self.connection_type_combo.set_item(self.item.client.client_type)
        self.grid_layout.addWidget(QLabel("Connection Type:"))
        self.grid_layout.addWidget(self.connection_type_combo)

        self.connection_widgets_layout = CustomGridLayout()
        self.grid_layout.addLayout(self.connection_widgets_layout)

        self.setLayout(self.grid_layout)

        # Set initial state and connect signals:
        self.update_item()

        self.connection_type_combo.currentIndexChanged.connect(self.update_item)
        # self.host_line_edit.textChanged.connect(self.update_item)
        # self.port_spinbox.textChanged.connect(self.update_item)
        # self.serial_port_line_edit.textChanged.connect(self.update_item)
        # self.serial_baudrate_combo.currentIndexChanged.connect(self.update_item)

    def update_connection_fields(self):
        # Clear all items' layout:
        self.clear_layout(self.connection_widgets_layout)
        self.grid_layout.removeItem(self.connection_widgets_layout)

        if self.connection_type_combo.currentText() == "Modbus TCP":
            self.item.connection_client = ModbusClient(name=self.item.name)

            host_line_edit = QLineEdit(self.item.connection_client.tcp_host)
            self.connection_widgets_layout.add_widget(QLabel("Host/Port:"), host_line_edit)

            port_spinbox = QSpinBox()
            port_spinbox.setRange(1, 65535)
            port_spinbox.setValue(self.item.connection_client.tcp_port)
            self.connection_widgets_layout.add_widget(QLabel("Port:"), port_spinbox)

        elif self.connection_type_combo.currentText() == "Modbus RTU":
            self.item.connection_client = ModbusClient(name=self.item.name)

            serial_port_line_edit = QLineEdit(self.item.connection_client.serial_port)
            self.connection_widgets_layout.add_widget(QLabel("Serial Port:"), serial_port_line_edit)

            serial_baudrate_combo = CustomComboBox()
            serial_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
            index = serial_baudrate_combo.findText(str(self.item.connection_client.serial_baudrate))
            serial_baudrate_combo.setCurrentIndex(index)
            self.connection_widgets_layout.add_widget(QLabel("Baudrate:"), serial_baudrate_combo)

        self.grid_layout.addLayout(self.connection_widgets_layout)

    def clear_layout(self, layout):
        """Remove and delete all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def update_item(self):
        self.update_connection_fields()

        modbus_client = ModbusClient(
            name=self.item.name,
            client_type=self.connection_type_combo.currentText(),
            tcp_host=self.host_line_edit.text(),
            tcp_port=int(self.port_spinbox.text()),
            serial_port=self.serial_port_line_edit.text(),
            serial_baudrate=int(self.serial_baudrate_combo.currentText()),

        )
        self.model.update_item(client=modbus_client)


class CollectionRequestWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        connection_widget = CollectionConnectionTabWidget(model)
        detail_tabs.addTab(connection_widget, "Connection")

        main_layout.addWidget(detail_tabs)


class CollectionDetail(QWidget):
    def __init__(self, model):
        super().__init__()

        self.setMinimumSize(800, 600)

        self.setWindowTitle("Collection Details")

        self.model = model
        self.item = self.model.get_selected_item()

        main_layout = QVBoxLayout()

        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        # Title:
        self.title_label = IconTextWidget(self.item.name, QIcon(ITEMS[self.item.item_type]["icon"]))
        header_layout.addWidget(self.title_label)

        # Añadir la cabecera al layout principal
        main_layout.addWidget(header)

        splitter = QSplitter()

        # Detail
        self.detail_tabs = CollectionRequestWidget(model)

        # Fill splitter:
        splitter.addWidget(self.detail_tabs)

        main_layout.addWidget(splitter)
        main_layout.addStretch()

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(Collection(name="Collection Test"))
    window = CollectionDetail(model)
    window.show()
    sys.exit(app.exec())