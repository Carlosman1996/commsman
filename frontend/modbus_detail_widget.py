import struct
import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox
from PyQt6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIcon, QPainter
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QTableWidgetItem, QSplitter, QMenu)

from backend.core.backend_manager import BackendManager
from backend.protocols.modbus_handler import ModbusHandler
from frontend.model import Model
from frontend.models.modbus import ModbusRequest, ModbusClient
from frontend.common import ITEMS


FUNCTIONS_DICT = {
    "read": ["Read Holding Registers", "Read Input Registers", "Read Coils", "Read Discrete Inputs"],
    "write": ["Write Coil", "Write Coils", "Write Register", "Write Registers"]
}
FUNCTIONS = []
for functions in FUNCTIONS_DICT.values():
    FUNCTIONS += functions


class IconTextWidget(QWidget):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(75, 75)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(text)
        text_label.setFixedHeight(50)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(20)
        layout.addStretch(1)

        self.setStyleSheet("font-size: 16px; font-weight: bold;")


class CustomGridLayout(QGridLayout):
    def __init__(self, height=30, label_width=150, field_width=200):
        # TODO: all layouts must have this format for reusability and consistency
        super().__init__()
        self.height = height  # Maximum height
        self.label_width = label_width  # Maximum width for labels
        self.field_width = field_width  # Maximum width for fields
        self.table = []  # Store references to rows for visibility control
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def add_widget(self, label, field, column=0, index=None):
        label.setMaximumWidth(self.label_width)
        label.setMinimumWidth(self.label_width)
        label.setMaximumHeight(self.height)

        field.setMaximumWidth(self.field_width)
        field.setMinimumWidth(self.field_width)

        if isinstance(field, CustomTable):
            label.setContentsMargins(0, 5, 0, 0)
            alignment = Qt.AlignmentFlag.AlignTop
        else:
            alignment = None

        # Store the row (label and field) for visibility control
        if column >= len(self.table):
            self.table.append([])
            self.setColumnStretch(len(self.table) - 1, 1)
        if index:
            self.table[column][index] = (label, field)
        else:
            index = len(self.table[column])
            self.table[column].append((label, field))

        # Add the row to the layout
        if alignment:
            super().addWidget(label, index, column * 2, alignment)
            super().addWidget(field, index, (column * 2) + 1, alignment)
        else:
            super().addWidget(label, index, column * 2)
            super().addWidget(field, index, (column * 2) + 1)

    def show_row(self, column, index):
        """Show a specific row by index."""
        label, field = self.table[column][index]
        label.show()
        field.show()

    def hide_row(self, column, index):
        """Hide a specific row by index."""
        label, field = self.table[column][index]
        label.hide()
        field.hide()


class CustomTable(QTableWidget):
    def __init__(self, headers):
        super().__init__()

        self.setMaximumWidth(150 * len(headers))
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setStyleSheet("""
            QTableWidget {
                border: none; /* Remove any outer border */
            }
            QTableWidget::item:selected {
                background-color: #D5D7D6;
            }
            QToolTip {
                background-color: #D5D7D6;
            }
        """)

    def setItem(self, *args, **kwargs):
        super().setItem(*args, **kwargs)
        self.adjust_table_height()

    def insertRow(self, *args, **kwargs):
        super().insertRow(*args, **kwargs)
        self.adjust_table_height()

    def removeRow(self, *args, **kwargs):
        super().removeRow(*args, **kwargs)
        self.adjust_table_height()

    def adjust_table_height(self):
        header_height = self.horizontalHeader().height()
        row_height = self.rowHeight(0) if self.rowCount() > 0 else 30  # Default if no rows

        # Limit height to max_visible_rows
        visible_rows = self.rowCount() + 1

        # Total height = header + visible rows + padding
        total_height = header_height + (row_height * visible_rows) + 4

        self.setMaximumHeight(total_height)

    def set_items(self, items):
        for row, item in enumerate(items):
            self.setItem(row, 0, QTableWidgetItem(str(item)))

    def get_values(self):
        """Read values from the table and print them."""
        row_data = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if not item:
                row_data.append("")
            else:
                try:
                    row_data.append(int(item.text()))
                except:
                    row_data.append(item.text())
        return row_data


class CustomComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_item(self, item):
        # Set item based on class attribute
        if item in [self.itemText(i) for i in range(self.count())]:
            self.setCurrentText(item)
        else:
            self.setCurrentIndex(0)  # Fallback if not found


class CustomGroupBox(QGroupBox):
    def __init__(self, title, information):
        super().__init__(title)

        status_layout = QVBoxLayout()
        self.status_label = QLabel(information)
        status_layout.addWidget(self.status_label)
        self.setLayout(status_layout)


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
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float", "String"])
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
            self.quantity_spinbox.setRange(1, 247)

    def validate_all_inputs(self):
        self.values_table.blockSignals(True)

        data_type = self.data_type_combo.currentText()

        for row in range(self.values_table.rowCount()):
            # TODO: bug related with fails in first row
            item = self.values_table.item(row, 0)  # Get the item in the first column
            if not item:
                # Create a QTableWidgetItem if it's missing
                item = QTableWidgetItem()
                self.values_table.setItem(row, 0, item)

            # Validate the input
            is_valid, error_message = self.validate_input(item.text(), data_type)

            if not is_valid and error_message:  # If invalid and there's an error message
                item.setText(f"⚠ {item.text().replace('⚠ ', '')}")
                item.setToolTip(error_message)  # Show the error message as a tooltip

            elif not is_valid and not error_message:  # If invalid but no error message
                item.setText(item.text().replace("⚠ ", ""))
                item.setToolTip("Insert a value")  # Show a generic tooltip
                enable_execute_button = False

            else:  # If valid
                item.setText(item.text().replace("⚠ ", ""))
                item.setToolTip("")  # Clear tooltip

        self.values_table.clearSelection()
        self.values_table.blockSignals(False)

    def validate_input(self, text, data_type):
        """Validates input based on data type. Returns (is_valid, error_message)."""
        text = text.strip()
        if not text:
            return False, ""

        try:
            if data_type == "16-bit Integer":
                value = int(text)
                if not -32768 <= value <= 32767:
                    return False, "Value must be between -32768 and 32767"
            elif data_type == "16-bit Unsigned Integer":
                value = int(text)
                if not 0 <= value <= 65535:
                    return False, "Value must be between 0 and 65535"
            elif data_type == "32-bit Integer":
                value = int(text)
                if not -2147483648 <= value <= 2147483647:
                    return False, "Value must be between -2147483648 and 2147483647"
            elif data_type == "32-bit Unsigned Integer":
                value = int(text)
                if not 0 <= value <= 4294967295:
                    return False, "Value must be between 0 and 4294967295"
            elif data_type == "Hexadecimal":
                int(text, 16)
                return True, ""
            elif data_type == "Float":
                float(text)
                return True, ""
            elif data_type == "String":
                str(text)
                return True, ""
            else:
                return False, "Unknown data type"
        except ValueError or BaseException:
            return False, "Wrong format"
        except OverflowError:
            return False, "Value out of range"

        return True, ""

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
        self.validate_all_inputs()

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

        self.data_type_menu = CustomComboBox()
        self.data_type_menu.addItem("16-bit Integer")
        self.data_type_menu.addItem("16-bit Unsigned Integer")
        self.data_type_menu.addItem("32-bit Integer")
        self.data_type_menu.addItem("32-bit Unsigned Integer")
        self.data_type_menu.addItem("Hexadecimal")
        self.data_type_menu.addItem("Float")
        self.data_type_menu.addItem("String")
        self.data_type_menu.setMaximumWidth(200)
        data_type_label = QLabel("Data type:")

        data_type_label.setMaximumWidth(150)
        data_type_label.setMinimumWidth(150)
        data_type_label.setMaximumHeight(30)

        self.data_type_menu.setMaximumWidth(200)
        self.data_type_menu.setMinimumWidth(200)

        self.data_type_layout.addWidget(data_type_label)
        self.data_type_layout.addWidget(self.data_type_menu)
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
        self.status_message_label = QLabel("N/A")
        self.status_message_label.setWordWrap(True)
        self.elapsed_time_label = QLabel("N/A")
        self.timestamp_label = QLabel("N/A")
        general_info_layout.add_widget(QLabel("Status:"), self.status_label)
        general_info_layout.add_widget(QLabel("Status Message:"), self.status_message_label)
        general_info_layout.add_widget(QLabel("Elapsed Time:"), self.elapsed_time_label)
        general_info_layout.add_widget(QLabel("Timestamp:"), self.timestamp_label)
        general_info_group.setLayout(general_info_layout)
        metadata_layout.addWidget(general_info_group)

        # Headers and Data
        headers_group = QGroupBox("Headers and Data")
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
        headers_group.setLayout(headers_layout)
        metadata_layout.addWidget(headers_group)

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

        self.model.signal_update_item.connect(self.update_input_visibility)
        if self.item.last_response:
            self.process_response(self.item.last_response)

    def update_input_visibility(self):
        pass
        # Hide response tab in write registers operations:
        # response_tab_index = self.tabs.indexOf(self.response_tab)
        # if self.item.function in FUNCTIONS_DICT["write"]:
        #     self.tabs.removeTab(response_tab_index)
        # elif response_tab_index < 0:
        #     self.tabs.insertTab(0, self.response_tab, "Response")

    def process_response(self, response):
        self.elapsed_time_label.setText(str(response.get("elapsed_time")) + " ms")
        self.timestamp_label.setText(str(response.get("timestamp")))

        self.transaction_id_label.setText(str(response.get("transaction_id", "-")))
        self.protocol_id_label.setText(str(response.get("protocol_id", "-")))
        self.unit_id_label.setText(str(response.get("slave_id", "-")))
        self.function_code_label.setText(str(response.get("function_code", "-")))
        self.byte_count_label.setText(str(response.get("byte_count", "-")))

        self.raw_data_edit.setText(
            f"SEND: {response.get('raw_packet_send', '-')}\n\nRECV: {response.get('raw_packet_recv', '-')}")

        if response.get("error_message"):
            self.status_label.setText("Fail")
            self.status_label.setStyleSheet("color: red;")
            self.status_message_label.setText(
                f"Error: {response.get('error_message')}")
            self.error_data_edit.setText(
                f"Status: {self.status_label.text()}\n\nError: {response.get('error_message')}")
            self.error_data_edit.show()  # Show error group
            self.data_type_menu.hide()
            self.values_table.hide()  # Hide values table
        else:
            self.status_label.setText("Pass")
            self.status_label.setStyleSheet("color: green;")
            self.status_message_label.setText("-")
            self.values_table.setRowCount(len(response.get("registers")))
            for row, register in enumerate(response.get("registers")):
                self.values_table.setItem(row, 0, QTableWidgetItem(str(response.get("address") + row)))
                self.values_table.setItem(row, 1, QTableWidgetItem(str(register)))
            self.error_data_edit.hide()  # Show error group
            self.data_type_menu.show()
            self.values_table.show()  # Hide values table

        self.model.update_item(last_response=response)

    def update_data_type(self, action):
        """Update the data type and convert values accordingly."""
        data_type = action.text()

        # Sample raw data (replace with actual Modbus response)
        raw_values = [1234, 5678]

        # Convert values based on selected data type
        converted_values = []
        for value in raw_values:
            if data_type == "16-bit Integer":
                converted_values.append(self.convert_to_16bit_int(value))
            elif data_type == "16-bit Unsigned Integer":
                converted_values.append(self.convert_to_16bit_uint(value))
            elif data_type == "32-bit Integer":
                converted_values.append(self.convert_to_32bit_int([value, 0]))  # Example for 32-bit
            elif data_type == "32-bit Unsigned Integer":
                converted_values.append(self.convert_to_32bit_uint([value, 0]))  # Example for 32-bit
            elif data_type == "Hexadecimal":
                converted_values.append(self.convert_to_hex(value))
            elif data_type == "Float":
                converted_values.append(self.convert_to_float([value, 0]))  # Example for 32-bit float
            elif data_type == "String":
                converted_values.append(self.convert_to_string(value))

        # Update the table with converted values
        self.update_table(converted_values)

    # Conversion functions
    def convert_to_16bit_int(self, value):
        """Convert to 16-bit signed integer."""
        return struct.unpack('>h', value.to_bytes(2, byteorder='big'))[0]

    def convert_to_16bit_uint(self, value):
        """Convert to 16-bit unsigned integer."""
        return value

    def convert_to_32bit_int(self, values):
        """Convert to 32-bit signed integer."""
        return struct.unpack('>i', bytes(values))[0]

    def convert_to_32bit_uint(self, values):
        """Convert to 32-bit unsigned integer."""
        return struct.unpack('>I', bytes(values))[0]

    def convert_to_hex(self, value):
        """Convert to hexadecimal string."""
        return hex(value)

    def convert_to_float(self, values):
        """Convert to 32-bit float."""
        return struct.unpack('>f', bytes(values))[0]

    def convert_to_string(self, value):
        """Convert to string."""
        return str(value)


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
        if not self.item.last_response:
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
        request_result = modbus_handler.execute_request(function=self.item.function,
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