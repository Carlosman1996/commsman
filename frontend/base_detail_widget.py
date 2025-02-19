from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter

from frontend.common import ITEMS
from frontend.components.components import IconTextWidget


class ExecuteButton(QPushButton):
    def __init__(self, backend_running: bool):
        super().__init__("Run")
        self.run = True
        if backend_running:
            self.set_stop()
        else:
            self.set_run()

    def set_stop(self):
        self.run = False
        self.setText("Stop")
        self.setStyleSheet("""
            QPushButton {
                background-color: red;
                color: white;
            }
            QPushButton:hover {
                background-color: red;
                color: white;
            }
        """)

    def set_run(self):
        self.run = True
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
        self.execute_button = ExecuteButton(self.controller.running)
        header_layout.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Añadir la cabecera al layout principal
        main_layout.addWidget(header)

        self.splitter = QSplitter()

        main_layout.addWidget(self.splitter)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.execute_button.clicked.connect(self.execute)

    def execute(self):
        if self.execute_button.run:
            self.execute_button.set_stop()

            # Create and start the backend_manager thread
            self.controller.signal_finish.connect(self.on_finished)
            self.controller.start()
        else:
            self.controller.signal_finish.emit()
            self.execute_button.set_run()

    def on_finished(self):
        self.execute_button.set_run()
