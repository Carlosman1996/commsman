import sys

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

from frontend.model import Model
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
        self.resize(1100, 600)

        # Define general model:
        self.model = Model()

        # Divide window in two sections:
        self.main_window_sections_splitter = QSplitter()

        # Left section:
        self.project_structure_section = ProjectStructureSection(self.model)
        self.project_structure_section.tree_view.selectionModel().selectionChanged.connect(self.set_detail_section)

        # Right section:
        self.detail_section = self.set_detail_section()
        self.detail_section.setMinimumSize(500, 600)

        # Add sections to splitter
        self.main_window_sections_splitter.addWidget(self.project_structure_section)
        self.main_window_sections_splitter.addWidget(self.detail_section)

        # Main layout:
        self.main_window_layout = QVBoxLayout()
        self.main_window_layout.addWidget(self.main_window_sections_splitter)

        # Configure central widget:
        container = QWidget()
        container.setLayout(self.main_window_layout)
        self.setCentralWidget(container)

        # Load data:
        self.model.load_tree_data()

    def set_detail_section(self):
        item = self.project_structure_section.get_selected_item()
        self.model.set_selected_item(item)

        if item is not None and item.parent() is not None:  # Check if it is not the root
            if item.item_type == "Modbus":
                self.detail_section = ModbusDetail(self.model)
            else:
                self.detail_section = QLabel("Not implemented yet")
        else:
            self.detail_section = QLabel("Select an item to display information")

        if self.main_window_sections_splitter.count() > 1:
            self.main_window_sections_splitter.replaceWidget(1, self.detail_section)
        return self.detail_section

    def closeEvent(self, *args, **kwargs):
        """Override the close event to perform custom actions."""
        # Close all handlers before exit:
        self.model.protocol_client_manager.close_all_handlers()
        super().closeEvent(*args, **kwargs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme=f"{FRONTEND_PATH}/theme.xml", css_file=f"{FRONTEND_PATH}/styles.css")

    window = MainWindow()
    window.show()

    app.exec()
