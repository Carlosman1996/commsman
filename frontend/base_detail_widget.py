from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter

from backend.backend_manager import BackendManager
from frontend.common import ITEMS
from frontend.components.components import IconTextWidget


class ExecuteButton(QPushButton):
    def __init__(self):
        super().__init__("Run")
        self.set_run()

    def set_running(self):
        self.setEnabled(False)
        self.setText("Running")
        self.setStyleSheet("""
            QPushButton {
                color: red;
                border: 2px solid red;
            }
            QPushButton:hover {
                background-color: red;
                color: white;
            }
        """)

    def set_run(self):
        # Re-enable the "Execute" button
        self.setEnabled(True)
        self.setText("Run")
        self.setStyleSheet("""
            QPushButton {
                color: green;
                border: 2px solid green;  /* Green border */
            }
            QPushButton:hover {
                background-color: green;
                color: white;
            }
        """)


class BaseDetail(QWidget):
    def __init__(self, model, controller):
        super().__init__()

        self.setMinimumSize(800, 600)

        self.setWindowTitle("Detail View")

        self.model = model
        self.item = self.model.get_selected_item()

        self.controller = controller

        main_layout = QVBoxLayout()

        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        # Title:
        self.title_label = IconTextWidget(self.item.name, QIcon(ITEMS[self.item.item_type]["icon"]), QSize(75, 50))
        header_layout.addWidget(self.title_label)

        # Execute request:
        self.execute_button = ExecuteButton()
        header_layout.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Añadir la cabecera al layout principal
        main_layout.addWidget(header)

        self.splitter = QSplitter()

        main_layout.addWidget(self.splitter)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.execute_button.clicked.connect(self.execute)

    def execute(self):
        self.execute_button.set_running()

        # Create and start the backend_manager thread
        self.controller.signal_request_progress.connect(self.update_progress)
        self.controller.signal_requests_finished.connect(self.on_finished)
        self.controller.start()

    def update_progress(self, response):
        # Update the progress label
        print(response)

    def on_finished(self):
        self.execute_button.set_run()
