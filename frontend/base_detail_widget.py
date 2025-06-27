from abc import abstractmethod

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QSizePolicy, QLabel

from frontend.common import ITEMS, get_model_value, convert_time, convert_timestamp
from frontend.components.components import IconTextWidget, CustomGridLayout, InfoBox, CustomTable


class ExecuteButton(QPushButton):
    def __init__(self, backend_running: bool, blocked: bool):
        super().__init__("Run")
        self.setFixedWidth(100)
        self.run = True
        if backend_running and blocked:
            self.set_blocked()
        elif backend_running:
            self.set_stop()
        else:
            self.set_run()

    def set_stop(self):
        self.setEnabled(True)
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
        self.setEnabled(True)
        self.run = True
        self.setText("Run")
        self.setStyleSheet("""
            QPushButton {
                background-color: #F8F8FF;
                color: green;
                border: 2px solid green;  /* Green border */
            }
            QPushButton:hover {
                background-color: green;
                color: white;
            }
        """)

    def set_blocked(self):
        self.setEnabled(False)
        self.setText("Blocked")
        self.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: white;
            }
            QPushButton:hover {
                background-color: orange;
                color: white;
            }
        """)



class BaseRequest(QWidget):

    def __init__(self, api_client, item, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.api_client = api_client
        self.item = item

    @abstractmethod
    def reload_data(self):
        raise NotImplementedError

    @abstractmethod
    def update_item(self):
        raise NotImplementedError

    @abstractmethod
    def update_view(self, data: dict):
        raise NotImplementedError


class BaseResult(QWidget):
    def __init__(self, api_client, item, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.api_client = api_client
        self.item = item
        self.item_last_result = self.item["last_result"]
        self.backend_running = False

        # Update the UI every 500 ms:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_backend_running)
        self.timer.start(500)

    def get_backend_running(self):
        self.api_client.get_running_threads(callback=self.reload_data)

    @abstractmethod
    def on_finished(self):
        pass

    def reload_data(self, data: dict):
        if self.backend_running:
            self.api_client.get_item_last_result_tree(item_id=self.item["item_id"], callback=self.update_view)

        # Update running flag after updating results to show last result:
        self.backend_running = bool(data["running_threads"])
        if not self.backend_running:
            self.on_finished()

    @abstractmethod
    def update_view(self, data: dict):
        raise NotImplementedError


class BaseDetail(BaseResult):
    def __init__(self, api_client, item):
        # BaseResult is needed because it inherits methods related with backend:
        super().__init__(api_client, item)

        self.setMinimumSize(500, 600)

        self.setWindowTitle("Detail View")

        self.header_height = 100

        main_layout = QVBoxLayout()

        # Set base splitter:
        splitter = QSplitter()
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Request side layout:
        self.request_splitter_section = QWidget()
        splitter.addWidget(self.request_splitter_section)
        self.request_layout = QVBoxLayout()
        self.request_splitter_section.setLayout(self.request_layout)
        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(self.header_height)
        header_layout = QHBoxLayout()
        header_widget.setLayout(header_layout)
        self.request_layout.addWidget(header_widget)
        # Title:
        self.title_label = IconTextWidget(self.item["name"], QIcon(ITEMS[self.item["item_handler"]]["icon"]), QSize(75, 50))
        header_layout.addWidget(self.title_label)
        # Execute button at right side:
        header_layout.addStretch(1)
        # Execute request:
        backend_running_other_item = bool(self.backend_running and self.item["item_id"] not in self.backend.running_threads)
        self.execute_button = ExecuteButton(backend_running=self.backend_running, blocked=backend_running_other_item)
        header_layout.addWidget(self.execute_button)

        # Request side layout:
        self.result_splitter_section = QWidget()
        self.result_splitter_section.setMinimumWidth(500)
        splitter.addWidget(self.result_splitter_section)
        self.result_layout = QVBoxLayout()
        self.result_splitter_section.setLayout(self.result_layout)
        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(self.header_height)
        header_layout = QHBoxLayout()
        header_widget.setLayout(header_layout)
        self.result_layout.addWidget(header_widget)
        # Last results:
        self.frame_result = InfoBox("")
        header_layout.addWidget(self.frame_result)
        self.frame_elapsed_time = InfoBox("")
        header_layout.addWidget(self.frame_elapsed_time)
        self.frame_timestamp = InfoBox("")
        header_layout.addWidget(self.frame_timestamp)
        self.frame_iterations = InfoBox("")
        header_layout.addWidget(self.frame_iterations)
        self.frame_results = InfoBox("")
        header_layout.addWidget(self.frame_results)
        # All items at left side:
        header_layout.addStretch(1)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Set initial state and connect signals:
        self.update_view(data=self.item["last_result"])

        self.execute_button.clicked.connect(self.execute)

    def execute(self):
        if self.execute_button.run:
            # Backend running should be initialized to True to read, at least, one result from backend. If not, in fast
            # executions the results might not be reported:
            self.backend_running = True
            self.execute_button.set_stop()

            # Create and start the backend_manager thread
            self.api_client.run_item(item_id=self.item["item_id"])
        else:
            # Stop the backend_manager thread
            self.api_client.stop_item(item_id=self.item["item_id"])
            self.execute_button.set_run()

    def on_finished(self):
        self.execute_button.set_run()

    def update_view(self, data: dict):
        if data is None:
            self.result_splitter_section.setVisible(False)
            return
        else:
            self.result_splitter_section.setVisible(True)

        self.frame_result.setText(get_model_value(data, "result"))
        self.frame_elapsed_time.setText(convert_time(get_model_value(data, "elapsed_time", 0)))
        self.frame_timestamp.setText(convert_timestamp(get_model_value(data, "timestamp")))
        self.frame_iterations.setText(f"Iterations: {get_model_value(data, "iterations")}")
        self.frame_results.setText(f"Total OK / KO: "
                                   f"{get_model_value(data, "total_ok")} / "
                                   f"{get_model_value(data, "total_failed")}")
