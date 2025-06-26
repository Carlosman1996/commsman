from PyQt6.QtCore import Qt
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

        # Set initial state and connect signals:
        self.update_view(load_data=True)

    def update_view(self, load_data=False, result=None):
        if result:
            if len(self.item["results_history"]) > 0:
                if self.item["results_history"][0]["item_id"] == result["item_id"]:
                    self.item["results_history"][0] = result
                else:
                    self.item["results_history"].insert(0, result)
            else:
                self.item["results_history"].append(result)
        results_history = self.item["results_history"][:10]

        self.table.clear()
        self.table.setRowCount(len(results_history))
        row = 0
        for result in results_history:
            result_widget = QTableWidgetItem(str(result["result"]))
            result_widget.setIcon(get_icon(result["result"]))
            self.table.setItem(row, 0, result_widget)
            elapsed_time_widget = QTableWidgetItem(convert_time(result["elapsed_time"]))
            self.table.setItem(row, 1, elapsed_time_widget)
            timestamp_widget = QTableWidgetItem(convert_timestamp(result["timestamp"]))
            self.table.setItem(row, 2, timestamp_widget)
            row += 1
