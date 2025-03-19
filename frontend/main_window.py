import sys
import time

from PyQt6.QtCore import Qt
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

from backend.backend_manager import BackendManager
from frontend.collection_detail_widget import CollectionDetail
from frontend.project_structure_section import ProjectStructureSection
from qt_material import apply_stylesheet
from frontend.modbus_detail_widget import ModbusDetail

from utils.common import FRONTEND_PATH


class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QSizePolicy()
        self.setSizePolicy(size_policy)
        self.adjustSize()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Commsman")
        # self.showMaximized()
        self.resize(1280, 720)

        # Define general controller:
        self.backend = BackendManager()
        self.repository = self.backend.repository

        # Divide window in two sections:
        self.main_window_sections_splitter = QSplitter()

        # Left section:
        self.project_structure_section = ProjectStructureSection(self.repository)
        self.project_structure_section.tree_view.selectionModel().selectionChanged.connect(self.set_detail_section)

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

    def set_detail_section(self):
        item_data = self.project_structure_section.get_selected_item_data()
        self.repository.set_selected_item(item_data)
        item = self.repository.get_selected_item()

        if item is not None:
            if item.item_handler == "ModbusRequest":
                self.detail_section = ModbusDetail(self.backend)
            elif item.item_handler == "Collection":
                self.detail_section = CollectionDetail(self.backend)
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
        # Close all handlers before exit:
        self.backend.protocol_client_manager.close_all_handlers()

        # Wait until backend stops:
        self.backend.signal_finish.emit()
        while self.backend.running:
            time.sleep(0.5)

        super().closeEvent(*args, **kwargs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme=f"{FRONTEND_PATH}/theme.xml", css_file=f"{FRONTEND_PATH}/styles.css")

    window = MainWindow()
    window.show()

    app.exec()
