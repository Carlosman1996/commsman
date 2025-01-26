import sys

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QMessageBox, QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QFormLayout)

from frontend.models.modbus import ModbusRequest
from frontend.common import ITEMS


class IconTextWidget(QWidget):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(32, 32)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(text)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(5)
        layout.addStretch(1)


class ModbusConnectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        connection_group = QGroupBox("Modbus Connection") # Groupbox for the connection
        connection_layout = QFormLayout() # Form layout for labels and inputs
        connection_group.setLayout(connection_layout)

        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["TCP", "RTU"])
        connection_layout.addRow("Connection Type:", self.connection_type_combo)

        self.host_input = QLineEdit("127.0.0.1")  # Default localhost
        connection_layout.addRow("Host/Port:", self.host_input)

        self.port_spinbox = QSpinBox()
        self.port_spinbox.setMinimum(1)
        self.port_spinbox.setMaximum(65535)
        self.port_spinbox.setValue(502)  # Default Modbus TCP port
        connection_layout.addRow("Port:", self.port_spinbox)

        self.serial_port_input = QLineEdit("/dev/ttyUSB0")
        connection_layout.addRow("Serial Port:", self.serial_port_input)
        self.serial_baudrate_combo = QComboBox()
        self.serial_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        connection_layout.addRow("Baudrate:", self.serial_baudrate_combo)
        self.connection_type_combo.currentIndexChanged.connect(self.update_connection_fields)
        self.update_connection_fields()

        main_layout = QVBoxLayout()
        main_layout.addWidget(connection_group)
        self.setLayout(main_layout)

    def update_connection_fields(self):
        if self.connection_type_combo.currentText() == "TCP":
            self.host_input.show()
            self.port_spinbox.show()
            self.serial_port_input.hide()
            self.serial_baudrate_combo.hide()
        elif self.connection_type_combo.currentText() == "RTU":
            self.host_input.hide()
            self.port_spinbox.hide()
            self.serial_port_input.show()
            self.serial_baudrate_combo.show()

    def get_connection_parameters(self):
        connection_type = self.connection_type_combo.currentText()
        if connection_type == "TCP":
            host = self.host_input.text()
            port = self.port_spinbox.value()
            return {"type": "tcp", "host": host, "port": port}
        elif connection_type == "RTU":
            port = self.serial_port_input.text()
            baudrate = int(self.serial_baudrate_combo.currentText())
            return {"type": "rtu", "port": port, "baudrate": baudrate}
        return None


class ModbusRequestWidget(QWidget):
    def __init__(self, dataclass):
        super().__init__()

        self.functions_dict = {
            "read": ["Read Holding Registers", "Read Input Registers", "Read Coils", "Read Discrete Inputs"],
            "write": ["Write Coils", "Write Registers"]
        }
        self.functions = []
        for functions in self.functions_dict.values():
            self.functions += functions

        main_layout = QVBoxLayout()

        form_layout = QGridLayout()

        self.function_combo = QComboBox()
        self.function_combo.addItems(self.functions)
        form_layout.addWidget(QLabel("Modbus Function:"), 0, 0)
        form_layout.addWidget(self.function_combo, 0, 1)

        self.address_spinbox = QSpinBox()
        form_layout.addWidget(QLabel("Address:"), 1, 0)
        form_layout.addWidget(self.address_spinbox, 1, 1)

        self.quantity_spinbox = QSpinBox()
        self.quantity_label = QLabel("Count:")
        self.quantity_spinbox.setMinimum(1) # Ensure at least 1
        form_layout.addWidget(self.quantity_label, 2, 0)
        form_layout.addWidget(self.quantity_spinbox, 2, 1)

        self.slave_id_spinbox = QSpinBox()
        self.slave_id_spinbox.setMinimum(1) # Ensure at least 1
        form_layout.addWidget(QLabel("Slave ID:"), 3, 0)
        form_layout.addWidget(self.slave_id_spinbox, 3, 1)

        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float"])
        form_layout.addWidget(QLabel("Data Type:"), 4, 0)
        form_layout.addWidget(self.data_type_combo, 4, 1)

        self.value_label = QLabel("Values to Write:") #Changed the label
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(1)
        self.values_table.setHorizontalHeaderLabels(["Value"])
        self.values_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.values_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        form_layout.addWidget(self.value_label, 5, 0)
        form_layout.addWidget(self.values_table, 5, 1)

        main_layout.addLayout(form_layout)

        self.execute_button = QPushButton("Execute Request")
        main_layout.addWidget(self.execute_button)

        self.tabs = QTabWidget()

        self.raw_data_text = QPlainTextEdit()
        self.tabs.addTab(self.raw_data_text, "Raw Data")

        self.parsed_data_text = QPlainTextEdit()
        self.tabs.addTab(self.parsed_data_text, "Parsed Data")

        self.log_text = QTextEdit()
        self.tabs.addTab(self.log_text, "Log/Console")

        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        # Signals:
        self.function_combo.currentIndexChanged.connect(self.update_input_visibility) # Connect the signal
        self.quantity_spinbox.valueChanged.connect(self.update_table_rows)
        self.data_type_combo.currentIndexChanged.connect(self.validate_all_inputs)
        self.values_table.itemChanged.connect(self.validate_all_inputs)

        self.update_table_rows(1)
        self.update_input_visibility()

    def update_input_visibility(self):
        selected_function = self.function_combo.currentText()

        if selected_function in self.functions_dict["write"]:
            self.value_label.show()
            self.values_table.show()
        else:
            self.value_label.hide()
            self.values_table.hide()

        self.validate_all_inputs()

    def validate_all_inputs(self):
        data_type = self.data_type_combo.currentText()
        enable_execute_button = True
        for row in range(self.values_table.rowCount()):
            item = self.values_table.item(row, 0)
            if item:
                is_valid, error_message = self.validate_input(item.text(), data_type)
                if not is_valid and error_message:
                    palette = item.tableWidget().palette()
                    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.red)
                    item.setForeground(palette.color(QPalette.ColorRole.Text))
                    item.setToolTip(error_message)
                    enable_execute_button = False
                elif not is_valid and not error_message:
                    item.setForeground(Qt.GlobalColor.gray)
                    item.setToolTip("Insert a value")
                    enable_execute_button = False
                else:
                    item.setForeground(Qt.GlobalColor.black)
                    item.setToolTip("")

        self.values_table.clearSelection()
        self.execute_button.setEnabled(enable_execute_button)

    def update_table_rows(self, value):
        current_rows = self.values_table.rowCount()
        if value > current_rows:
            for _ in range(value - current_rows):
                self.values_table.insertRow(self.values_table.rowCount())
        elif value < current_rows:
            for _ in range(current_rows - value):
                self.values_table.removeRow(self.values_table.rowCount() - 1)


class ModbusDetail(QWidget):
    def __init__(self, dataclass):
        super().__init__()

        self.setWindowTitle("Modbus Request Details")

        main_layout = QVBoxLayout()

        self.title_label = IconTextWidget(dataclass.name, QIcon(ITEMS[dataclass.type]["icon"]))
        main_layout.addWidget(self.title_label)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Connection Tab
        self.connection_widget = ModbusConnectionWidget()
        self.tabs.addTab(self.connection_widget, "Connection")

        # Request Tab
        self.connection_widget = ModbusRequestWidget(dataclass)
        self.tabs.addTab(self.connection_widget, "Request")

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dataclass = ModbusRequest(name="Demo")
    window = ModbusDetail(dataclass)
    window.show()
    sys.exit(app.exec())