from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QVBoxLayout, QTableWidgetItem, QLabel)

from frontend.base_detail_widget import BaseResult
from frontend.common import convert_time, get_icon, convert_timestamp
from frontend.components.components import CustomTable


class HistoryTabWidget(BaseResult):

    def __init__(self, api_client, item):
        super().__init__(api_client, item)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Define table:
        self.table = CustomTable(headers=["Result", "Elapsed Time", "Timestamp"],
                                 editable=False,
                                 stretch=False)

        self.main_layout.addWidget(self.table)
        self.main_layout.addStretch()

        # Update the UI every 1 s:
        self.timer.timeout.connect(self.reload_data)
        self.timer.start(1000)

        # Set initial state and connect signals:
        self.update_view(data=self.item_results_history)

    def reload_data(self):
        self.api_client.get_item_results_history(item_id=self.item["item_id"],
                                                 request_id=self.request_id,
                                                 callback=self.update_view)

    def update_view(self, data: dict):
        if data is None:
            return
        else:
            self.item_results_history = data

        self.table.clear()
        self.table.setRowCount(len(self.item_results_history))
        row = 0
        for result in self.item_results_history:
            result_widget = QTableWidgetItem(str(result["result"]))
            result_widget.setIcon(get_icon(result["result"]))
            self.table.setItem(row, 0, result_widget)
            elapsed_time_widget = QTableWidgetItem(convert_time(result["elapsed_time"]))
            self.table.setItem(row, 1, elapsed_time_widget)
            timestamp_widget = QTableWidgetItem(convert_timestamp(result["timestamp"]))
            self.table.setItem(row, 2, timestamp_widget)
            row += 1
