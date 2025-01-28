import sys

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QMessageBox, QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QFormLayout, QTableWidgetItem)

from frontend.models.modbus import ModbusRequest
from frontend.common import ITEMS


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
        text_label.setFixedHeight(75)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(20)
        layout.addStretch(1)


class CustomFormLayout(QFormLayout):
    def __init__(self, height=30, label_width=150, field_width=200):
        super().__init__()
        self.height = height  # Maximum height
        self.label_width = label_width  # Maximum width for labels
        self.field_width = field_width  # Maximum width for fields
        self.rows = []  # Store references to rows for visibility control

    def addRow(self, label, field):
        label.setMaximumWidth(self.label_width)
        label.setMinimumWidth(self.label_width)
        label.setMaximumHeight(self.height)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        field.setMaximumWidth(self.field_width)
        field.setMinimumWidth(self.field_width)
        if not isinstance(field, QTableWidget):
            field.setMaximumHeight(self.height)

        # Add the row to the layout
        super().addRow(label, field)
        # Store the row (label and field) for visibility control
        self.rows.append((label, field))

    def showRow(self, index):
        """Show a specific row by index."""
        if 0 <= index < len(self.rows):
            label, field = self.rows[index]
            label.show()
            field.show()

    def hideRow(self, index):
        """Hide a specific row by index."""
        if 0 <= index < len(self.rows):
            label, field = self.rows[index]
            label.hide()
            field.hide()


class ModbusConnectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        connection_group = QGroupBox("Modbus Connection") # Groupbox for the connection
        self.form_layout = CustomFormLayout()
        connection_group.setLayout(self.form_layout)

        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["TCP", "RTU"])
        self.form_layout.addRow(QLabel("Connection Type:"), self.connection_type_combo)

        self.form_layout.addRow(QLabel("Host/Port:"), QLineEdit("127.0.0.1"))

        port_spinbox = QSpinBox()
        port_spinbox.setMinimum(1)
        port_spinbox.setMaximum(65535)
        port_spinbox.setValue(502)  # Default Modbus TCP port
        self.form_layout.addRow(QLabel("Port:"), port_spinbox)

        self.form_layout.addRow(QLabel("Serial Port:"), QLineEdit("/dev/ttyUSB0"))

        serial_baudrate_combo = QComboBox()
        serial_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.form_layout.addRow(QLabel("Baudrate:"), serial_baudrate_combo)

        self.connection_type_combo.currentIndexChanged.connect(self.update_connection_fields)
        self.update_connection_fields()

        main_layout = QVBoxLayout()
        main_layout.addWidget(connection_group)
        self.setLayout(main_layout)

    def update_connection_fields(self):
        if self.connection_type_combo.currentText() == "TCP":
            self.form_layout.showRow(1)
            self.form_layout.showRow(2)
            self.form_layout.hideRow(3)
            self.form_layout.hideRow(4)
        elif self.connection_type_combo.currentText() == "RTU":
            self.form_layout.hideRow(1)
            self.form_layout.hideRow(2)
            self.form_layout.showRow(3)
            self.form_layout.showRow(4)


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

        self.form_layout = CustomFormLayout()

        self.function_combo = QComboBox()
        self.function_combo.addItems(self.functions)
        self.form_layout.addRow(QLabel("Modbus Function:"), self.function_combo)

        self.address_spinbox = QSpinBox()
        self.form_layout.addRow(QLabel("Address:"), self.address_spinbox)

        self.quantity_spinbox = QSpinBox()
        self.form_layout.addRow(QLabel("Count:"), self.quantity_spinbox)

        self.slave_id_spinbox = QSpinBox()
        self.slave_id_spinbox.setMinimum(1)
        self.form_layout.addRow(QLabel("Slave ID:"), self.slave_id_spinbox)

        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float"])
        self.form_layout.addRow(QLabel("Data Type:"), self.data_type_combo)

        self.values_table = QTableWidget()
        self.values_table.setColumnCount(1)
        self.values_table.setHorizontalHeaderLabels(["Value"])
        self.values_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.values_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.values_table.setStyleSheet("""
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
        self.form_layout.addRow(QLabel("Values to Write:"), self.values_table)

        main_layout.addLayout(self.form_layout)

        self.execute_button = QPushButton("Execute Request")
        main_layout.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)

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
            self.form_layout.showRow(5)
        else:
            self.form_layout.hideRow(5)

        self.validate_all_inputs()

    def validate_all_inputs(self):
        data_type = self.data_type_combo.currentText()
        enable_execute_button = True

        for row in range(self.values_table.rowCount()):
            item = self.values_table.item(row, 0)  # Get the item in the first column
            if not item:
                # Create a QTableWidgetItem if it's missing
                item = QTableWidgetItem()
                self.values_table.setItem(row, 0, item)

            # Validate the input
            is_valid, error_message = self.validate_input(item.text(), data_type)

            if not is_valid and error_message:  # If invalid and there's an error message
                # TODO: not working
                item.setForeground(Qt.GlobalColor.red)  # Set text color to red
                # TODO: open tooltip as default
                item.setToolTip(error_message)  # Show the error message as a tooltip
                enable_execute_button = False

            elif not is_valid and not error_message:  # If invalid but no error message
                # TODO: not working
                item.setForeground(Qt.GlobalColor.gray)  # Set text color to gray
                item.setToolTip("Insert a value")  # Show a generic tooltip
                enable_execute_button = False

            else:  # If valid
                item.setForeground(Qt.GlobalColor.black)  # Reset text color to black
                item.setToolTip("")  # Clear tooltip

        self.values_table.clearSelection()
        self.execute_button.setEnabled(enable_execute_button)

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
            else:
                return False, "Unknown data type"
        except ValueError or BaseException:
            return False, "Wrong format"
        except OverflowError:
            return False, "Value out of range"

        return True, ""

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

        self.setMinimumSize(500, 600)

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

        # TODO: split view in title, tabs (connection and detail), results

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dataclass = ModbusRequest(name="Demo")
    window = ModbusDetail(dataclass)
    window.show()
    sys.exit(app.exec())