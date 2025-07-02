import argparse
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QSplitter,
    QLabel,
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QSizePolicy
)

from frontend.api_client import ApiClient
from frontend.collection_detail_widget import CollectionDetail
from frontend.common import ITEMS
from frontend.project_structure_section import ProjectStructureSection
from qt_material import apply_stylesheet
from frontend.modbus_detail_widget import ModbusDetail

from config import FRONTEND_PATH, load_app_config


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy()
        self.setSizePolicy(size_policy)
        self.adjustSize()


class MainWindow(QMainWindow):
    def __init__(self, host: str, port: int):
        super().__init__()

        self.setWindowTitle("Commsman")
        self.setWindowIcon(QIcon(ITEMS["App"]["icon"]))
        # self.showMaximized()
        self.resize(1920, 1080)

        # Set API client:
        self.api_client = ApiClient(host=host, port=port)

        # Divide window in two sections:
        self.main_window_sections_splitter = QSplitter()

        # Left section:
        self.project_structure_section = ProjectStructureSection(self.api_client)
        self.project_structure_section.tree_view.selectionModel().selectionChanged.connect(self.get_item_request)

        # Right section:
        self.detail_section = self.set_detail_section()

        # Add sections to splitter_uuid
        self.main_window_sections_splitter.addWidget(self.project_structure_section)
        self.main_window_sections_splitter.addWidget(self.detail_section)

        # Set stretch factors
        self.main_window_sections_splitter.setStretchFactor(0, 0)  # Index 0 (will not expand)
        self.main_window_sections_splitter.setStretchFactor(1, 1)  # Index 1 (will expand)

        # Main layout:
        self.main_window_layout = QVBoxLayout()
        self.main_window_layout.addWidget(self.main_window_sections_splitter)

        # Configure central widget:
        container = QWidget()
        container.setLayout(self.main_window_layout)
        self.setCentralWidget(container)

    def get_item_request(self):
        item_id = self.project_structure_section.get_selected_item_data()
        if item_id:
            self.api_client.get_item_request(item_id, callback=self.set_detail_section)

    def set_detail_section(self, item = None, *args, **kwargs):
        if item is not None:
            if item["item_handler"] == "ModbusRequest":
                self.detail_section = ModbusDetail(self.api_client, item)
            elif item["item_handler"] == "Collection":
                self.detail_section = CollectionDetail(self.api_client, item)
            else:
                self.detail_section = QLabel("Not implemented yet")
        else:
            self.detail_section = QLabel("Select an item to display information")

        if self.main_window_sections_splitter.count() > 1:
            self.main_window_sections_splitter.replaceWidget(1, self.detail_section)
            self.main_window_sections_splitter.setStretchFactor(1, 1)  # Index 1 (will expand)
        return self.detail_section

    def closeEvent(self, *args, **kwargs):
        """Override the close event to perform custom actions."""
        # Wait until backend stops:
        self.api_client.stop_item(item_id=0)

        super().closeEvent(*args, **kwargs)


def run(host: str, port: int):
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme=f"{FRONTEND_PATH}/fixtures/theme.xml", css_file=f"{FRONTEND_PATH}/fixtures/styles.css")

    window = MainWindow(host=host, port=port)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    config = load_app_config(find_port=False)

    parser = argparse.ArgumentParser(description="Start frontend.")
    parser.add_argument("--host", help="API host.", default=config["api"]["host"])
    parser.add_argument("--port", help="API port.", default=config["api"]["port"])
    args = parser.parse_args()

    run(host=args.host, port=args.port)
