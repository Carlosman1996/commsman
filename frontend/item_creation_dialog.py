from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLabel, QVBoxLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class ItemCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Item")
        self.setFixedSize(300, 200)

        # Grid layout for selection
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Add buttons/icons for each type
        self.buttons = {}
        item_types = ["Folder", "Modbus", "MQTT", "HTTP", "Custom"]
        for i, item in enumerate(item_types):
            button = QPushButton(item)
            button.clicked.connect(lambda _, t=item: self.select_item(t))
            button.setFixedSize(80, 50)
            grid_layout.addWidget(button, i // 3, i % 3)
            self.buttons[item] = button

        # Dialog layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select the type of item to create:", alignment=Qt.AlignmentFlag.AlignCenter))
        layout.addLayout(grid_layout)

        # Add Cancel button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.selected_item = None

    def select_item(self, item_type):
        self.selected_item = item_type
        self.accept()
