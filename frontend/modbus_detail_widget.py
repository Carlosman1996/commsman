import sys

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QMessageBox, QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView)

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


class ModbusRequestDetails(QWidget):
    def __init__(self, dataclass):
        super().__init__()

        self.functions_dict = {
            "read": ["Read Holding Registers", "Read Input Registers", "Read Coils", "Read Discrete Inputs"],
            "write": ["Write Coils", "Write Registers"]
        }
        self.functions = []
        for functions in self.functions_dict.values():
            self.functions += functions

        self.setWindowTitle("Modbus Request Details")

        main_layout = QVBoxLayout()

        self.title_label = IconTextWidget(dataclass.name, QIcon(ITEMS[dataclass.type]["icon"]))

        main_layout.addWidget(self.title_label)

        form_layout = QGridLayout()

        self.function_combo = QComboBox()
        self.function_combo.addItems(self.functions)
        form_layout.addWidget(QLabel("Modbus Function:"), 0, 0)
        form_layout.addWidget(self.function_combo, 0, 1)

        self.address_spinbox = QSpinBox()
        form_layout.addWidget(QLabel("Address:"), 1, 0)
        form_layout.addWidget(self.address_spinbox, 1, 1)

        self.slave_id_spinbox = QSpinBox()
        self.slave_id_spinbox.setMinimum(1) # Ensure at least 1
        form_layout.addWidget(QLabel("Slave ID:"), 3, 0)
        form_layout.addWidget(self.slave_id_spinbox, 3, 1)

        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["16-bit Integer", "16-bit Unsigned Integer", "32-bit Integer", "32-bit Unsigned Integer", "Hexadecimal", "Float"])
        form_layout.addWidget(QLabel("Data Type:"), 4, 0)
        form_layout.addWidget(self.data_type_combo, 4, 1)

        self.quantity_spinbox = QSpinBox()
        self.quantity_label = QLabel("Count:")
        self.quantity_spinbox.setMinimum(1) # Ensure at least 1
        form_layout.addWidget(self.quantity_label, 2, 0)
        form_layout.addWidget(self.quantity_spinbox, 2, 1)

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

    def show_error_message(self, message):
        """Displays an error message dialog."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dataclass = ModbusRequest(name="Demo")
    window = ModbusRequestDetails(dataclass)
    window.show()
    sys.exit(app.exec())