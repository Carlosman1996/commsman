import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout, QPlainTextEdit,
                             QMessageBox, QHBoxLayout)

from frontend.common import ITEMS


class IconTextWidget(QWidget):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(32, 32)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            print(f"Error loading icon: {icon_path}")

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
        self.function_combo.currentIndexChanged.connect(self.update_input_visibility) #Connect the signal
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
        self.data_type_combo.addItems(["16-bit Integer", "32-bit Integer", "Float", "String", "Hex"])
        form_layout.addWidget(QLabel("Data Type:"), 4, 0)
        form_layout.addWidget(self.data_type_combo, 4, 1)

        self.quantity_spinbox = QSpinBox()
        self.quantity_label = QLabel("Count:")
        self.quantity_spinbox.setMinimum(1) # Ensure at least 1
        form_layout.addWidget(self.quantity_label, 2, 0)
        form_layout.addWidget(self.quantity_spinbox, 2, 1)

        self.value_label = QLabel("Value to Write:")
        self.value_input = QLineEdit()
        self.value_input.textChanged.connect(self.update_execute_button_state) #Connect the signal
        form_layout.addWidget(self.value_label, 5, 0)
        form_layout.addWidget(self.value_input, 5, 1)

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

        self.update_input_visibility()
        self.update_execute_button_state()

    def update_input_visibility(self):
        selected_function = self.function_combo.currentText()

        if selected_function in self.functions_dict["write"]:
            self.value_label.show()
            self.value_input.show()
        else:
            self.value_label.hide()
            self.value_input.hide()

        if selected_function in self.functions:
            self.quantity_label.show()
            self.quantity_spinbox.show()
        else:
            self.quantity_label.hide()
            self.quantity_spinbox.hide()

        self.update_execute_button_state()  # Call this function to update the button state

    def update_execute_button_state(self):
        selected_function = self.function_combo.currentText()
        if selected_function in self.functions_dict["write"]:
            if self.value_input.text().strip() == "": #Check if the text is empty or contains only spaces
                self.execute_button.setEnabled(False)
            else:
                self.execute_button.setEnabled(True)
        else:
            self.execute_button.setEnabled(True) #Enable the button if it is not a write function


    def clear_results(self):
        self.raw_data_text.clear()
        self.parsed_data_text.clear()
        self.log_text.clear()

    def show_error_message(self, message):
        """Displays an error message dialog."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModbusRequestDetails()
    window.show()
    sys.exit(app.exec())