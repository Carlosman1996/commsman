from abc import abstractmethod

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QSizePolicy, QFrame, QGridLayout, \
    QLabel, QGroupBox

from frontend.common import ITEMS, get_model_value, convert_time
from frontend.components.components import IconTextWidget, CustomGridLayout, InfoBox


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
                background-color: #F8F8FF;
                color: green;
                border: 2px solid green;  /* Green border */
            }
            QPushButton:hover {
                background-color: green;
                color: white;
            }
        """)


class BaseRequest(QWidget):

    def __init__(self, repository, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.repository = repository
        self.item = self.repository.get_selected_item()

    def update_sequence(self):
        self.update_item()
        self.update_view()

    def reload_data(self):
        self.item = self.repository.get_selected_item()

    @abstractmethod
    def update_item(self):
        pass

    @abstractmethod
    def update_view(self):
        pass


class BaseResult(QWidget):
    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend
        self.repository = self.backend.repository
        self.item = self.backend.repository.get_selected_item()

        self.backend.signal_request_finished.connect(self.reload_data)

    def reload_data(self, item_id, result):
        if self.item.item_id == item_id:
            self.update_view(result=result)

    @abstractmethod
    def update_view(self, load_data: bool = False, result: object = None):
        raise NotImplementedError


class BaseDetail(BaseResult):
    def __init__(self, backend):
        # BaseResult is needed because it inherits methods related with backend:
        super().__init__(backend)

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
        self.title_label = IconTextWidget(self.item.name, QIcon(ITEMS[self.item.item_handler]["icon"]), QSize(75, 50))
        header_layout.addWidget(self.title_label)
        # Execute request:
        self.execute_button = ExecuteButton(self.backend.running)
        header_layout.addWidget(self.execute_button)
        # All items at left side:
        header_layout.addStretch(1)

        # Request side layout:
        self.result_splitter_section = QWidget()
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
        # All items at left side:
        header_layout.addStretch(1)

        # Set stretch factors
        splitter.setStretchFactor(0, 0)  # Index 0 (will not expand)
        splitter.setStretchFactor(1, 1)  # Index 1 (will expand)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Set initial state and connect signals:
        self.update_view(load_data=True)

        self.execute_button.clicked.connect(self.execute)

    def execute(self):
        if self.execute_button.run:
            self.execute_button.set_stop()

            # Create and start the backend_manager thread
            self.backend.signal_finish.connect(self.on_finished)
            self.backend.start()
        else:
            self.backend.signal_finish.emit()
            self.execute_button.set_run()

    def on_finished(self):
        self.execute_button.set_run()

    def update_view(self, load_data=False, result=None):
        if load_data:
            result = self.item.last_result
        if result is None:
            self.result_splitter_section.setVisible(False)
            return
        else:
            self.result_splitter_section.setVisible(True)

        self.frame_result.setText(get_model_value(result, "result"))
        self.frame_elapsed_time.setText(convert_time(get_model_value(result, "elapsed_time", 0)))
        self.frame_timestamp.setText(get_model_value(result, "timestamp"))
