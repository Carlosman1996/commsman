from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter

from frontend.common import ITEMS
from frontend.components.components import IconTextWidget


class BaseDetail(QWidget):
    def __init__(self, model):
        super().__init__()

        self.setMinimumSize(800, 600)

        self.setWindowTitle("Detail View")

        self.model = model
        self.item = self.model.get_selected_item()

        main_layout = QVBoxLayout()

        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        # Title:
        self.title_label = IconTextWidget(self.item.name, QIcon(ITEMS[self.item.item_type]["icon"]), QSize(75, 50))
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

        self.splitter = QSplitter()

        main_layout.addWidget(self.splitter)
        main_layout.addStretch()

        self.setLayout(main_layout)
