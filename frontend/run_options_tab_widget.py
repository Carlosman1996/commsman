from PyQt6.QtWidgets import (QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.base_detail_widget import BaseRequest
from frontend.components.components import CustomGridLayout


class RunOptionsTabWidget(BaseRequest):

    def __init__(self, repository):
        super().__init__(repository)

        self.repository = repository
        self.item = self.repository.get_selected_item()

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

        self.grid_layout.signal_update_item.connect(self.update_sequence)

    def update_item(self):
        if self.item.run_options:
            run_options = {
                "name": self.item.name,
                "polling_interval": int(self.polling_interval_label.text()),
                "delayed_start": int(self.delayed_start.text()),
            }
            self.repository.update_item(item_handler=self.item.run_options.item_handler, item_id=self.item.run_options.item_id, **run_options)
        else:
            self.repository.create_client_item(
                item_name=self.item.name,
                item_handler="RunOptions",
                parent=self.item,
            )

    def update_view(self, load_data: bool = False):
        if load_data and not self.item.run_options:
            self.update_sequence()

        self.polling_interval_label.setValue(self.item.run_options.polling_interval)
        self.delayed_start.setValue(self.item.run_options.delayed_start)
