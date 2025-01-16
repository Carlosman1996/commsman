import sys
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLabel, QVBoxLayout, QLineEdit, QDialogButtonBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt


class ItemCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Item")
        self.setFixedSize(400, 300)

        # Title Text
        title_label = QLabel("Create New Item")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Input field for item name
        name_label = QLabel("Item Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter name for the new item")
        self.name_input.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Grid layout for item types
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Add buttons/icons for each type
        self.buttons = {}
        item_types = ["Folder", "Modbus"]
        for i, item in enumerate(item_types):
            button = QPushButton(item)
            button.clicked.connect(lambda _, t=item: self.select_item(t))
            button.setFixedSize(80, 50)
            grid_layout.addWidget(button, i // 3, i % 3)
            self.buttons[item] = button

        # Dialog layout
        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addSpacing(10)

        # Add input field for name
        name_layout = QVBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Add grid of buttons
        layout.addSpacing(15)
        layout.addWidget(QLabel("Select Item Type:", alignment=Qt.AlignmentFlag.AlignLeft))
        layout.addLayout(grid_layout)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Attributes to hold the selected item and name
        self.selected_item = None
        self.item_name = None

    def select_item(self, item_type):
        """Set the selected item type."""
        self.selected_item = item_type

    def validate_and_accept(self):
        """Validate inputs and show an error message if needed."""
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Error", "You must enter a name for the item.")
            return
        if not self.selected_item:
            self.show_error("Error", "You must select an item type.")
            return
        self.item_name = name
        super().accept()

    def show_error(self, title, message):
        """Display an error message."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ItemCreationDialog()
    window.show()

    app.exec()
