from functools import partial

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.components.components import CustomGridLayout, CustomComboBox
from frontend.models.modbus import ModbusRtuClient, ModbusTcpClient
from frontend.models.run_options import RunOptions


class RunOptionsTabWidget(QWidget):

    def __init__(self, model):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        main_layout = QVBoxLayout()

        self.grid_layout = CustomGridLayout()

        # self.polling_label = QSpinBox()
        # self.polling_label.setRange(0, 999999)

        self.polling_interval_label = QSpinBox()
        self.polling_interval_label.setRange(0, 999999)

        self.delayed_start = QSpinBox()
        self.delayed_start.setRange(0, 999999)

        # self.grid_layout.add_widget(QLabel("Polling:"), self.polling_label)
        self.grid_layout.add_widget(QLabel("Polling interval:"), self.polling_interval_label)
        self.grid_layout.add_widget(QLabel("Delayed start:"), self.delayed_start)

        # Add the grid layout to the main layout
        main_layout.addLayout(self.grid_layout)

        self.setLayout(main_layout)

        # Set initial state and connect signals:
        self.update_view(load_data=True)

        self.grid_layout.signal_update_item.connect(partial(self.update_view, load_data=False))

    def update_view(self, load_data: bool = False):
        if self.item.run_options is None:
            run_options = RunOptions(self.item.name)
        else:
            run_options = self.item.run_options

        if load_data:
            self.polling_interval_label.setValue(run_options.polling_interval)
            self.delayed_start.setValue(run_options.delayed_start)

        self.update_item()

    def update_item(self):
        run_options = RunOptions(
            name=self.item.name,
            polling_interval=int(self.polling_interval_label.text()),
            delayed_start=int(self.delayed_start.text()),
        )

        self.model.update_item(run_options=run_options)
