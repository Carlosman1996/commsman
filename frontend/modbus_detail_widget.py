import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QSpinBox,
                             QTabWidget, QTextEdit, QHBoxLayout, QGroupBox,
                             QTableWidgetItem)

from backend.handlers.custom_modbus_handler import convert_value_after_sending
from frontend.base_detail_widget import BaseDetail, BaseResult, BaseRequest
from frontend.common import get_model_value, convert_time
from frontend.components.components import CustomGridLayout, CustomTable, CustomComboBox
from frontend.connection_tab_widget import ConnectionTabWidget
from frontend.run_options_tab_widget import RunOptionsTabWidget

FUNCTIONS_DICT = {
    "read": ["Read Holding Registers", "Read Input Registers", "Read Coils", "Read Discrete Inputs"],
    "write": ["Write Coil", "Write Coils", "Write Register", "Write Registers"]
}
FUNCTIONS = []
for functions in FUNCTIONS_DICT.values():
    FUNCTIONS += functions


class ModbusRequestTabWidget(BaseRequest):
    def __init__(self, model):
        super().__init__(model)

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
        self.update_table_rows_view()
        self.values_table.set_items(self.item.values)
        self.grid_layout.add_widget(QLabel("Values to Write:"), self.values_table)

        self.setLayout(self.grid_layout)

        # Set initial state and connect signals:
        self.update_view()

        self.grid_layout.signal_update_item.connect(self.update_sequence)

    def update_item(self):
        update_data = {
            "function": self.function_combo.currentText(),
            "address": int(self.address_spinbox.text()),
            "count": int(self.quantity_spinbox.text()),
            "slave": int(self.unit_id_spinbox.text()),
            "data_type": self.data_type_combo.currentText(),
            "values": self.values_table.get_values(),
        }
        self.model.update_item(item_uuid=self.item.uuid, **update_data)

    def update_view(self):
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

        self.update_table_rows_view()

    def update_table_rows_view(self):
        value = self.quantity_spinbox.value()
        current_rows = self.values_table.rowCount()
        if value > current_rows:
            for _ in range(value - current_rows):
                self.values_table.insertRow(current_rows)
        elif value < current_rows:
            for index in range(current_rows - value):
                self.values_table.removeRow(current_rows - index - 1)


class ModbusRequestWidget(QWidget):

    def __init__(self, model, controller):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set tabs:
        detail_tabs = QTabWidget()

        self.connection_widget = ConnectionTabWidget(model, controller, ["Inherit from parent", "Modbus TCP", "Modbus RTU"])
        detail_tabs.addTab(self.connection_widget, "Connection")

        self.request_widget = ModbusRequestTabWidget(model)
        detail_tabs.addTab(self.request_widget, "Request")

        detail_tabs.addTab(RunOptionsTabWidget(model), "Run options")

        main_layout.addWidget(detail_tabs)


class ModbusResponseWidget(BaseResult):

    def __init__(self, model, controller):
        super().__init__(model, controller)

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
        self.result_layout = QVBoxLayout()
        self.response_tab.setLayout(self.result_layout)

        # Response values table (initially hidden)
        self.values_table = CustomTable(["Address", "Value"])
        self.result_layout.addWidget(self.values_table)

        # Data type menu button
        self.data_type_layout = QHBoxLayout()
        self.data_type_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.data_type_combo = CustomComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float", "Double", "String"])
        self.data_type_combo.set_item(getattr(self.item.last_result, "data_type", "16-bit Integer"))
        self.data_type_combo.setMaximumWidth(200)
        self.data_type_combo.setMinimumWidth(200)
        self.data_type_label = QLabel("Show data type:")

        self.data_type_label.setMaximumWidth(150)
        self.data_type_label.setMinimumWidth(150)
        self.data_type_label.setMaximumHeight(30)

        self.data_type_layout.addWidget(self.data_type_label)
        self.data_type_layout.addWidget(self.data_type_combo)
        self.result_layout.addLayout(self.data_type_layout)

        # Error display (initially hidden)
        self.error_data_edit = QTextEdit()
        self.error_data_edit.setReadOnly(True)
        self.error_data_edit.setStyleSheet("color: red;")
        self.result_layout.addWidget(self.error_data_edit)
        self.error_data_edit.hide()  # Hide error group by default

        self.result_layout.addStretch()

        self.tabs.addTab(self.response_tab, "Response")

        # Metadata Tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout()
        metadata_tab.setLayout(metadata_layout)

        # General Information
        general_info_group = QGroupBox("General Information")
        general_info_layout = CustomGridLayout()
        self.status_label = QLabel("N/A")
        self.protocol_label = QLabel("N/A")
        self.elapsed_time_label = QLabel("N/A")
        self.timestamp_label = QLabel("N/A")
        general_info_layout.add_widget(QLabel("Status:"), self.status_label)
        general_info_layout.add_widget(QLabel("Protocol:"), self.protocol_label)
        general_info_layout.add_widget(QLabel("Elapsed Time:"), self.elapsed_time_label)
        general_info_layout.add_widget(QLabel("Timestamp:"), self.timestamp_label)
        general_info_group.setLayout(general_info_layout)
        metadata_layout.addWidget(general_info_group)

        # Headers and Data
        self.headers_group = QGroupBox("Headers and Data")
        self.headers_layout = CustomGridLayout()
        self.transaction_id_label = QLabel("N/A")
        self.protocol_id_label = QLabel("N/A")
        self.unit_id_label = QLabel("N/A")
        self.function_code_label = QLabel("N/A")
        self.byte_count_label = QLabel("N/A")
        self.crc_label = QLabel("N/A")
        self.headers_layout.add_widget(QLabel("Transaction ID:"), self.transaction_id_label)
        self.headers_layout.add_widget(QLabel("Protocol ID:"), self.protocol_id_label)
        self.headers_layout.add_widget(QLabel("Unit ID:"), self.unit_id_label)
        self.headers_layout.add_widget(QLabel("Function Code:"), self.function_code_label)
        self.headers_layout.add_widget(QLabel("Byte Count:"), self.byte_count_label)
        self.headers_layout.add_widget(QLabel("CRC:"), self.crc_label)
        self.headers_group.setLayout(self.headers_layout)
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
        self.tabs.addTab(raw_data_tab, "Raw Data")

        # Set initial state and connect signals:
        self.update_view()

        self.data_type_combo.currentTextChanged.connect(self.update_table)

    def get_response_data(self):
        def get_value(key, replace_if_none: str = "-"):
            return get_model_value(self.item.last_result, key, replace_if_none)

        return {
            "name": get_value("name"),
            "item_type": get_value("item_type"),
            "parent": get_value("parent"),
            "result": get_value("result"),
            "elapsed_time": convert_time(get_value("elapsed_time", 0)),
            "timestamp": get_value("timestamp"),
            "error_message": get_value("error_message", ""),
            "client_type": get_value("client_type"),
            "slave": get_value("slave"),
            "transaction_id": get_value("transaction_id"),
            "crc": get_value("crc"),
            "protocol_id": get_value("protocol_id"),
            "function_code": get_value("function_code"),
            "address": get_value("address"),
            "registers": get_value("registers"),
            "raw_packet_recv": get_value("raw_packet_recv", ""),
            "raw_packet_send": get_value("raw_packet_send", ""),
            "data_type": get_value("data_type", "16-bit Integer"),
            "byte_count": get_value("byte_count"),
        }

    def update_view(self):
        result = self.item.last_result
        if result is None or result.result == "Pending":
            return

        response = self.get_response_data()

        self.protocol_label.setText(response["client_type"])
        self.elapsed_time_label.setText(response["elapsed_time"])
        self.timestamp_label.setText(response["timestamp"])

        if response["client_type"] == "Modbus TCP":
            self.headers_layout.show_row(0, 0)
            self.headers_layout.show_row(0, 1)
            self.transaction_id_label.setText(response["transaction_id"])
            self.protocol_id_label.setText(response["protocol_id"])
        else:
            self.headers_layout.hide_row(0, 0)
            self.headers_layout.hide_row(0, 1)

        self.unit_id_label.setText(response["slave"])
        self.function_code_label.setText(response["function_code"])
        self.byte_count_label.setText(response["byte_count"])
        if response["client_type"] == "Modbus RTU":
            self.headers_layout.show_row(0, 5)
            self.crc_label.setText(response["crc"])
        else:
            self.headers_layout.hide_row(0, 5)

        self.raw_data_edit.setText(f"SEND: {response["raw_packet_send"]}\n\nRECV: {response["raw_packet_recv"]}")

        if response["result"] == "Failed":
            self.data_type_label.hide()
            self.data_type_combo.hide()
            self.values_table.hide()

            self.status_label.setText(response["result"])
            self.status_label.setStyleSheet("color: red;")
            self.error_data_edit.setText(
                f"Status: {self.status_label.text()}\n\nError: {response["error_message"]}")
            self.error_data_edit.show()  # Show error group
        else:
            self.error_data_edit.hide()
            self.data_type_label.show()
            self.data_type_combo.show()
            self.values_table.show()

            self.status_label.setText(response["result"])
            self.status_label.setStyleSheet("color: green;")
            self.data_type_combo.set_item(response["data_type"])
            self.update_table()

    def update_table(self):
        result = self.item.last_result
        if result is None or result.result == "Pending":
            return

        self.item.last_result.data_type = self.data_type_combo.currentText()
        response = self.get_response_data()

        data_type = self.data_type_combo.currentText()
        self.values_table.clear()

        # TODO: move logic to backend
        address_values = convert_value_after_sending(data_type, int(response["address"]), response["registers"])
        self.values_table.setRowCount(len(list(address_values.keys())))
        row = 0
        for address, value in address_values.items():
            address_item = QTableWidgetItem(str(address))
            self.values_table.setItem(row, 0, address_item)
            value_item = QTableWidgetItem(str(value))
            self.values_table.setItem(row, 1, value_item)
            row += 1


class ModbusDetail(BaseDetail):
    def __init__(self, model, controller):
        super().__init__(model, controller)

        # Detail
        self.request_tabs = ModbusRequestWidget(model, controller)

        # Results
        self.results_tabs = ModbusResponseWidget(model, controller)

        # Fill splitter:
        self.request_layout.addWidget(self.request_tabs)
        self.result_layout.addWidget(self.results_tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = Model()
    model.set_selected_item(ModbusRequest(name="Request"))
    window = ModbusDetail(model)
    window.show()
    sys.exit(app.exec())