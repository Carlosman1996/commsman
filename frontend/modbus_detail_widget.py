import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QPushButton,
                             QTabWidget, QTextEdit, QHBoxLayout, QGroupBox,
                             QTableWidgetItem, QSplitter)

from backend.modbus_handler import ModbusHandler, convert_value_after_sending
from frontend.components.components import CustomGridLayout, CustomTable, IconTextWidget, CustomComboBox
from frontend.model import Model
from frontend.models.modbus import ModbusRequest, ModbusClient, ModbusResponse
from frontend.common import ITEMS


FUNCTIONS_DICT = {
    "read": ["Read Holding Registers", "Read Input Registers", "Read Coils", "Read Discrete Inputs"],
    "write": ["Write Coil", "Write Coils", "Write Register", "Write Registers"]
}
FUNCTIONS = []
for functions in FUNCTIONS_DICT.values():
    FUNCTIONS += functions



class ModbusConnectionTabWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        self.grid_layout = CustomGridLayout()

        self.connection_type_combo = CustomComboBox()
        self.connection_type_combo.addItems(["TCP", "RTU"])
        self.connection_type_combo.set_item(self.item.client.client_type)
        self.grid_layout.add_widget(QLabel("Connection Type:"), self.connection_type_combo)

        self.host_line_edit = QLineEdit(self.item.client.tcp_host)
        self.grid_layout.add_widget(QLabel("Host/Port:"), self.host_line_edit)

        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1, 65535)
        self.port_spinbox.setValue(self.item.client.tcp_port)
        self.grid_layout.add_widget(QLabel("Port:"), self.port_spinbox)

        self.serial_port_line_edit = QLineEdit(self.item.client.serial_port)
        self.grid_layout.add_widget(QLabel("Serial Port:"), self.serial_port_line_edit)

        self.serial_baudrate_combo = CustomComboBox()
        self.serial_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        index = self.serial_baudrate_combo.findText(str(self.item.client.serial_baudrate))
        self.serial_baudrate_combo.setCurrentIndex(index)
        self.grid_layout.add_widget(QLabel("Baudrate:"), self.serial_baudrate_combo)
        self.setLayout(self.grid_layout)

        # Set initial state and connect signals:
        self.update_item()

        self.connection_type_combo.currentIndexChanged.connect(self.update_item)
        self.host_line_edit.textChanged.connect(self.update_item)
        self.port_spinbox.textChanged.connect(self.update_item)
        self.serial_port_line_edit.textChanged.connect(self.update_item)
        self.serial_baudrate_combo.currentIndexChanged.connect(self.update_item)

    def update_connection_fields(self):
        if self.connection_type_combo.currentText() == "TCP":
            self.grid_layout.show_row(0, 1)
            self.grid_layout.show_row(0, 2)
            self.grid_layout.hide_row(0, 3)
            self.grid_layout.hide_row(0, 4)
        elif self.connection_type_combo.currentText() == "RTU":
            self.grid_layout.hide_row(0, 1)
            self.grid_layout.hide_row(0, 2)
            self.grid_layout.show_row(0, 3)
            self.grid_layout.show_row(0, 4)

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


class ModbusRequestTabWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        self.grid_layout = CustomGridLayout()

        self.function_combo = CustomComboBox()
        self.function_combo.addItems(FUNCTIONS)
        self.function_combo.set_item(self.item.function)
        self.grid_layout.add_widget(QLabel("Modbus Function:"), self.function_combo)

        self.address_spinbox = QSpinBox()
        self.address_spinbox.setRange(1, 999999)
        self.address_spinbox.setValue(self.item.address)
        self.grid_layout.add_widget(QLabel("Address:"), self.address_spinbox)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 999999)
        self.quantity_spinbox.setValue(self.item.count)
        self.grid_layout.add_widget(QLabel("Count:"), self.quantity_spinbox)

        self.unit_id_spinbox = QSpinBox()
        self.unit_id_spinbox.setRange(1, 247)
        self.unit_id_spinbox.setValue(self.item.slave)
        self.grid_layout.add_widget(QLabel("Unit ID:"), self.unit_id_spinbox)

        self.data_type_combo = CustomComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float", "Double", "String"])
        self.data_type_combo.set_item(self.item.data_type)
        self.grid_layout.add_widget(QLabel("Data Type:"), self.data_type_combo)

        self.values_table = CustomTable(["Value"])
        self.update_table_rows()
        self.values_table.set_items(self.item.values)
        self.grid_layout.add_widget(QLabel("Values to Write:"), self.values_table)

        self.setLayout(self.grid_layout)

        # Set initial state and connect signals:
        self.update_item()

        self.function_combo.currentIndexChanged.connect(self.update_item)
        self.address_spinbox.valueChanged.connect(self.update_item)
        self.quantity_spinbox.valueChanged.connect(self.update_item)
        self.unit_id_spinbox.valueChanged.connect(self.update_item)
        self.data_type_combo.currentIndexChanged.connect(self.update_item)
        self.values_table.itemChanged.connect(self.update_item)

    def update_input_visibility(self):
        selected_function = self.function_combo.currentText()

        if selected_function in FUNCTIONS_DICT["write"]:
            self.grid_layout.show_row(0, 5)
            if selected_function in ["Write Coil", "Write Register"]:
                self.quantity_spinbox.setRange(1, 1)
            else:
                self.quantity_spinbox.setRange(1, 247)
        else:
            self.grid_layout.hide_row(0, 5)
            self.values_table.clear()
            self.quantity_spinbox.setRange(1, 247)

    def update_table_rows(self):
        value = self.quantity_spinbox.value()
        current_rows = self.values_table.rowCount()
        if value > current_rows:
            for _ in range(value - current_rows):
                self.values_table.insertRow(current_rows)
        elif value < current_rows:
            for index in range(current_rows - value):
                self.values_table.removeRow(current_rows - index - 1)

    def update_item(self):
        self.update_input_visibility()
        self.update_table_rows()

        update_data = {
            "function": self.function_combo.currentText(),
            "address": int(self.address_spinbox.text()),
            "count": int(self.quantity_spinbox.text()),
            "slave": int(self.unit_id_spinbox.text()),
            "data_type": self.data_type_combo.currentText(),
            "values": self.values_table.get_values(),
        }

        self.model.update_item(**update_data)


class ModbusRequestWidget(QWidget):
    def __init__(self, model):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        connection_widget = ModbusConnectionTabWidget(model)
        detail_tabs.addTab(connection_widget, "Connection")

        connection_widget = ModbusRequestTabWidget(model)
        detail_tabs.addTab(connection_widget, "Request")

        main_layout.addWidget(detail_tabs)


class ModbusResponseWidget(QWidget):

    def __init__(self, model):
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
        self.response_tab = QWidget()
        self.response_layout = QVBoxLayout()
        self.response_tab.setLayout(self.response_layout)

        # Response values table (initially hidden)
        self.values_table = CustomTable(["Address", "Value"])
        self.response_layout.addWidget(self.values_table)

        # Data type menu button
        self.data_type_layout = QHBoxLayout()
        self.data_type_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.data_type_combo = CustomComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float", "Double", "String"])
        if self.item.last_response:
            self.data_type_combo.set_item(self.item.last_response.data_type)
        self.data_type_combo.setMaximumWidth(200)
        self.data_type_combo.setMinimumWidth(200)
        self.data_type_label = QLabel("Show data type:")

        self.data_type_label.setMaximumWidth(150)
        self.data_type_label.setMinimumWidth(150)
        self.data_type_label.setMaximumHeight(30)

        self.data_type_layout.addWidget(self.data_type_label)
        self.data_type_layout.addWidget(self.data_type_combo)
        self.response_layout.addLayout(self.data_type_layout)

        # Error display (initially hidden)
        self.error_data_edit = QTextEdit()
        self.error_data_edit.setReadOnly(True)
        self.error_data_edit.setStyleSheet("color: red;")
        self.response_layout.addWidget(self.error_data_edit)
        self.error_data_edit.hide()  # Hide error group by default

        self.response_layout.addStretch()

        self.tabs.addTab(self.response_tab, "Response")

        # Metadata Tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout()
        metadata_tab.setLayout(metadata_layout)

        # General Information
        general_info_group = QGroupBox("General Information")
        general_info_layout = CustomGridLayout()
        self.status_label = QLabel("N/A")
        self.elapsed_time_label = QLabel("N/A")
        self.timestamp_label = QLabel("N/A")
        general_info_layout.add_widget(QLabel("Status:"), self.status_label)
        general_info_layout.add_widget(QLabel("Elapsed Time:"), self.elapsed_time_label)
        general_info_layout.add_widget(QLabel("Timestamp:"), self.timestamp_label)
        general_info_group.setLayout(general_info_layout)
        metadata_layout.addWidget(general_info_group)

        # Headers and Data
        self.headers_group = QGroupBox("Headers and Data")
        headers_layout = CustomGridLayout()
        self.transaction_id_label = QLabel("N/A")
        self.protocol_id_label = QLabel("N/A")
        self.unit_id_label = QLabel("N/A")
        self.function_code_label = QLabel("N/A")
        self.byte_count_label = QLabel("N/A")
        headers_layout.add_widget(QLabel("Transaction ID:"), self.transaction_id_label)
        headers_layout.add_widget(QLabel("Protocol ID:"), self.protocol_id_label)
        headers_layout.add_widget(QLabel("Unit ID:"), self.unit_id_label)
        headers_layout.add_widget(QLabel("Function Code:"), self.function_code_label)
        headers_layout.add_widget(QLabel("Byte Count:"), self.byte_count_label)
        self.headers_group.setLayout(headers_layout)
        metadata_layout.addWidget(self.headers_group)

        self.tabs.addTab(metadata_tab, "Metadata")

        # Raw Data Tab
        raw_data_tab = QWidget()
        raw_data_layout = QVBoxLayout()
        raw_data_tab.setLayout(raw_data_layout)

        # Raw data display
        self.raw_data_edit = QTextEdit()
        self.raw_data_edit.setReadOnly(True)
        raw_data_layout.addWidget(self.raw_data_edit)

        self.data_type_combo.currentIndexChanged.connect(self.update_table)
        self.tabs.addTab(raw_data_tab, "Raw Data")

        self.process_response(load_data=True)

    def process_response(self, response=None, load_data=False):
        if not load_data:
            response_dataclass = ModbusResponse(name=self.item.name, **response)
            self.model.update_item(last_response=response_dataclass)
        else:
            if self.item.last_response is None:
                return

        self.elapsed_time_label.setText(str(self.item.last_response.elapsed_time) + " ms")
        self.timestamp_label.setText(str(self.item.last_response.timestamp))

        self.raw_data_edit.setText(
            f"SEND: {self.item.last_response.raw_packet_send}\n\nRECV: {self.item.last_response.raw_packet_recv}")

        if self.item.last_response.error_message:
            self.data_type_label.hide()
            self.data_type_combo.hide()
            self.values_table.hide()
            self.headers_group.setVisible(False)

            self.status_label.setText("Fail")
            self.status_label.setStyleSheet("color: red;")
            self.error_data_edit.setText(
                f"Status: {self.status_label.text()}\n\nError: {self.item.last_response.error_message}")
            self.error_data_edit.show()  # Show error group
        else:
            self.error_data_edit.hide()
            self.data_type_label.show()
            self.data_type_combo.show()
            self.values_table.show()
            self.headers_group.setVisible(True)

            self.transaction_id_label.setText(str(self.item.last_response.transaction_id))
            self.protocol_id_label.setText(str(self.item.last_response.protocol_id))
            self.unit_id_label.setText(str(self.item.last_response.slave))
            self.function_code_label.setText(str(self.item.last_response.function_code))
            self.byte_count_label.setText(str(self.item.last_response.byte_count))

            self.status_label.setText("Pass")
            self.status_label.setStyleSheet("color: green;")
            self.data_type_combo.set_item(self.item.last_response.data_type)
            self.update_table()

    def update_table(self):
        self.item.last_response.data_type = self.data_type_combo.currentText()
        self.model.update_item(last_response=self.item.last_response)

        data_type = self.data_type_combo.currentText()
        self.values_table.clear()

        address_values = convert_value_after_sending(data_type, self.item.last_response.address, self.item.last_response.registers)
        self.values_table.setRowCount(len(list(address_values.keys())))
        row = 0
        for address, value in address_values.items():
            address_item = QTableWidgetItem(str(address))
            self.values_table.setItem(row, 0, address_item)
            value_item = QTableWidgetItem(str(value))
            self.values_table.setItem(row, 1, value_item)
            row += 1


class ModbusDetail(QWidget):
    def __init__(self, model):
        super().__init__()

        self.setMinimumSize(800, 600)

        self.setWindowTitle("Modbus Request Details")

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

        # Execute request:
        self.execute_button = QPushButton("Execute")
        header_layout.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.execute_button.setStyleSheet("""
            QPushButton {
                color: green;
                border: 2px solid green;  /* Green border */
            }
            QPushButton:hover {
                background-color: green;
                color: white;
            }
        """)

        # Añadir la cabecera al layout principal
        main_layout.addWidget(header)

        splitter = QSplitter()

        # Detail
        self.detail_tabs = ModbusRequestWidget(model)

        # Results
        self.results_tabs = ModbusResponseWidget(model)
        if not isinstance(self.item.last_response, ModbusResponse):
            self.results_tabs.setVisible(False)

        # Fill splitter:
        splitter.addWidget(self.detail_tabs)
        splitter.addWidget(self.results_tabs)

        main_layout.addWidget(splitter)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Connect signals and slots
        self.execute_button.clicked.connect(self.execute)

    def execute(self):
        modbus_handler = ModbusHandler()
        modbus_handler.connect(host=self.item.client.tcp_host,
                               port=self.item.client.tcp_port)
        request_result = modbus_handler.execute_request(data_type=self.item.data_type,
                                                        function=self.item.function,
                                                        address=self.item.address,
                                                        count=self.item.count,
                                                        slave=self.item.slave,
                                                        values=[value for value in self.item.values])
        modbus_handler.disconnect()

        self.results_tabs.process_response(response=request_result)
        self.results_tabs.setVisible(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(ModbusRequest(name="Request"))
    window = ModbusDetail(model)
    window.show()
    sys.exit(app.exec())