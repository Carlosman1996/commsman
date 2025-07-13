import types
from abc import abstractmethod

from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QSizePolicy

from frontend.api.api_helper_mixin import ApiCallMixin
from frontend.common import ITEMS, get_model_value, convert_time, convert_timestamp
from frontend.components.components import IconTextWidget, InfoBox
from frontend.safe_base import SafeWidget


class ExecuteButton(QPushButton):
    def __init__(self, backend_running: bool, blocked: bool):
        super().__init__("Run")
        self.setFixedWidth(100)
        self.run = True
        if blocked:
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


class Base(SafeWidget, ApiCallMixin):

    def __init__(self, api_client, item, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.item = item
        self.timer = QTimer(self)

        self.setup_api_client(api_client)

    @abstractmethod
    def update_view(self, data: dict):
        raise NotImplementedError


class BaseRequest(Base):

    def __init__(self, api_client, item, *args, **kwargs):
        super().__init__(api_client, item, *args, **kwargs)

    @abstractmethod
    def update_item(self):
        raise NotImplementedError


class BaseResult(Base):
    def __init__(self, api_client, item, *args, **kwargs):
        super().__init__(api_client, item, *args, **kwargs)

        self.item = item
        self.item_last_result = self.item["last_result"]
        self.item_results_history = self.item["results_history"]
        self.running_threads = []
        self.backend_running = False

        # Update the UI every 500 ms:
        self.timer.timeout.connect(self.reload_data)
        self.timer.start(1000)

    def reload_data(self):
        if self.backend_running:
            self.call_api(api_method="get_item_last_result_tree",
                          item_id=self.item["item_id"],
                          callback=self.update_view)

        self.call_api(api_method="get_running_threads",
                      callback=self.set_backend_running_status)

    def set_backend_running_status(self, data):
        self.running_threads = data["running_threads"]
        self.backend_running = bool(self.running_threads)
        if self.backend_running:
            self.on_running()
        else:
            self.on_finished()

    @abstractmethod
    def on_running(self):
        pass

    @abstractmethod
    def on_finished(self):
        pass


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
        self.execute_button = ExecuteButton(backend_running=False, blocked=True)
        self.execute_button.setVisible(False)
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

    def execute(self, *args, **kwargs):
        if self.execute_button.run:
            # Backend running should be initialized to True to read, at least, one result from backend. If not, in fast
            # executions the results might not be reported:
            self.backend_running = True
            # Create and start the backend_manager thread
            self.call_api(api_method="run_item",
                          item_id=self.item["item_id"])
        else:
            # Stop the backend_manager thread
            self.call_api(api_method="stop_item",
                          item_id=self.item["item_id"])

    def on_finished(self):
        self.execute_button.set_run()

    def on_running(self):
        backend_running_other_item = bool(self.item["item_id"] not in self.running_threads)
        if backend_running_other_item:
            self.execute_button.set_blocked()
        else:
            self.execute_button.set_stop()

    def update_view(self, data: dict):

        if not self.execute_button.isVisible():
            self.execute_button.setVisible(True)

        if data is None:
            self.result_splitter_section.setVisible(False)
            return
        else:
            self.result_splitter_section.setVisible(True)

        self.frame_result.setText(get_model_value(data, "result"))
        self.frame_elapsed_time.setText(convert_time(get_model_value(data, "elapsed_time", 0)))
        self.frame_timestamp.setText(convert_timestamp(get_model_value(data, "timestamp")))
        self.frame_iterations.setText(f"Iterations: {get_model_value(data, 'iterations')}")
        self.frame_results.setText(f"Total OK / KO: "
                                   f"{get_model_value(data, 'total_ok')} / "
                                   f"{get_model_value(data, 'total_failed')}")
