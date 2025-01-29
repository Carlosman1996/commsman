import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QTableWidgetItem, QSplitter)

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
        text_label.setFixedHeight(50)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(20)
        layout.addStretch(1)

        self.setStyleSheet("font-size: 16px; font-weight: bold;")


class CustomGridLayout(QGridLayout):
    def __init__(self, height=30, label_width=150, field_width=200):
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
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        field.setMaximumWidth(self.field_width)
        field.setMinimumWidth(self.field_width)
        if not isinstance(field, QTableWidget):
            field.setMaximumHeight(self.height)

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
        label.setContentsMargins(0, 5, 0, 0)
        super().addWidget(label, index, column * 2, Qt.AlignmentFlag.AlignTop)
        super().addWidget(field, index, (column * 2) + 1, Qt.AlignmentFlag.AlignTop)

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


class ModbusConnectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.grid_layout = CustomGridLayout()

        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["TCP", "RTU"])
        self.grid_layout.add_widget(QLabel("Connection Type:"), self.connection_type_combo)

        self.grid_layout.add_widget(QLabel("Host/Port:"), QLineEdit("127.0.0.1"))

        port_spinbox = QSpinBox()
        port_spinbox.setMinimum(1)
        port_spinbox.setMaximum(65535)
        port_spinbox.setValue(502)  # Default Modbus TCP port
        self.grid_layout.add_widget(QLabel("Port:"), port_spinbox)

        self.grid_layout.add_widget(QLabel("Serial Port:"), QLineEdit("/dev/ttyUSB0"))

        serial_baudrate_combo = QComboBox()
        serial_baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.grid_layout.add_widget(QLabel("Baudrate:"), serial_baudrate_combo)

        self.connection_type_combo.currentIndexChanged.connect(self.update_connection_fields)
        self.update_connection_fields()

        self.setLayout(self.grid_layout)

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
        submain_layout = QHBoxLayout()

        self.grid_layout = CustomGridLayout()

        self.function_combo = QComboBox()
        self.function_combo.addItems(self.functions)
        self.grid_layout.add_widget(QLabel("Modbus Function:"), self.function_combo)

        self.address_spinbox = QSpinBox()
        self.grid_layout.add_widget(QLabel("Address:"), self.address_spinbox)

        self.quantity_spinbox = QSpinBox()
        self.grid_layout.add_widget(QLabel("Count:"), self.quantity_spinbox)

        self.slave_id_spinbox = QSpinBox()
        self.slave_id_spinbox.setMinimum(1)
        self.grid_layout.add_widget(QLabel("Slave ID:"), self.slave_id_spinbox)

        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float"])
        self.grid_layout.add_widget(QLabel("Data Type:"), self.data_type_combo)

        submain_layout.addLayout(self.grid_layout)

        self.table_layout = CustomGridLayout()
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
        self.table_layout.add_widget(QLabel("Values to Write:"), self.values_table)

        submain_layout.addLayout(self.table_layout)
        main_layout.addLayout(submain_layout)

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
            self.table_layout.show_row(0, 0)
        else:
            self.table_layout.hide_row(0, 0)

        self.validate_all_inputs()

    def validate_all_inputs(self):
        self.values_table.blockSignals(True)

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
                item.setText(f"⚠ {item.text()}")
                item.setToolTip(error_message)  # Show the error message as a tooltip
                enable_execute_button = False

            elif not is_valid and not error_message:  # If invalid but no error message
                item.setText(item.text().replace("⚠ ", ""))
                item.setToolTip("Insert a value")  # Show a generic tooltip
                enable_execute_button = False

            else:  # If valid
                item.setText(item.text().replace("⚠ ", ""))
                item.setToolTip("")  # Clear tooltip

        self.values_table.clearSelection()
        # self.execute_button.setEnabled(enable_execute_button)

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

        self.setMinimumSize(800, 600)

        self.setWindowTitle("Modbus Request Details")

        main_layout = QVBoxLayout()

        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        # Title:
        self.title_label = IconTextWidget(dataclass.name, QIcon(ITEMS[dataclass.type]["icon"]))
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

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Detail
        self.detail_tabs = QTabWidget()

        self.connection_widget = ModbusConnectionWidget()
        self.detail_tabs.addTab(self.connection_widget, "Connection")

        self.connection_widget = ModbusRequestWidget(dataclass)
        self.detail_tabs.addTab(self.connection_widget, "Request")

        # Results
        self.results_tabs = QTabWidget()

        self.raw_data_text = QPlainTextEdit()
        self.results_tabs.addTab(self.raw_data_text, "Raw Data")

        self.parsed_data_text = QPlainTextEdit()
        self.results_tabs.addTab(self.parsed_data_text, "Parsed Data")

        self.log_text = QTextEdit()
        self.results_tabs.addTab(self.log_text, "Log/Console")

        # Fill splitter:
        splitter.addWidget(self.detail_tabs)
        splitter.addWidget(self.results_tabs)

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dataclass = ModbusRequest(name="Demo")
    window = ModbusDetail(dataclass)
    window.show()
    sys.exit(app.exec())