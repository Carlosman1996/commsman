from PyQt6.QtWidgets import (QCheckBox, QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.base_detail_widget import BaseRequest
from frontend.components.components import CustomGridLayout


class RunOptionsTabWidget(BaseRequest):

    def __init__(self, api_client, item):
        super().__init__(api_client, item)

        main_layout = QVBoxLayout()

        self.grid_layout = CustomGridLayout()

        # self.polling_label = QSpinBox()
        # self.polling_label.setRange(0, 999999)

        self.polling_interval_label = QSpinBox()
        self.polling_interval_label.setRange(0, 999999)
        self.polling_interval_label.setValue(0)

        self.delayed_start = QSpinBox()
        self.delayed_start.setRange(0, 999999)
        self.delayed_start.setValue(0)

        self.continuous_monitoring = QCheckBox()

        # self.grid_layout.add_widget(QLabel("Polling:"), self.polling_label)
        self.grid_layout.add_widget(QLabel("Polling interval:"), self.polling_interval_label)
        self.grid_layout.add_widget(QLabel("Delayed start:"), self.delayed_start)
        self.grid_layout.add_widget(QLabel("Continuous monitoring:"), self.continuous_monitoring)

        # Add the grid layout to the main layout
        main_layout.addLayout(self.grid_layout)

        self.setLayout(main_layout)

        # Set initial state and connect signals:
        self.item_run_options = self.item["run_options"]
        self.update_view(data=self.item_run_options)

        self.grid_layout.signal_update_item.connect(self.update_item)

    def update_item(self):
        if self.item_run_options:
            run_options = {
                "name": self.item_run_options["name"],
                "polling_interval": int(self.polling_interval_label.text()),
                "delayed_start": int(self.delayed_start.text()),
                "continuous_monitoring": bool(self.continuous_monitoring.isChecked()),
            }

            self.call_api(api_method="update_item_from_handler",
                            item_handler=self.item_run_options["item_handler"],
                            item_id=self.item_run_options["item_id"],
                            **run_options,
                            callback=self.update_view
            )
        else:
            self.call_api(api_method="create_run_options_item",
                          item_name=self.item["name"],
                          item_handler="RunOptions",
                          parent_item_id=self.item["item_id"],
                          callback=self.update_view)

    def update_view(self, data: dict):
        if not data:
            self.update_item()
            return
        else:
            self.item_run_options = data

        self.grid_layout.blockSignals(True)

        self.polling_interval_label.setValue(self.item_run_options["polling_interval"])
        self.delayed_start.setValue(self.item_run_options["delayed_start"])
        self.continuous_monitoring.setChecked(self.item_run_options["continuous_monitoring"])

        self.grid_layout.blockSignals(False)
