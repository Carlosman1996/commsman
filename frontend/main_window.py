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
from PyQt6.QtQuick import QSGMaterial


from frontend.project_structure_section import ProjectStructureSection
from qt_material import apply_stylesheet
from frontend.modbus_detail_widget import ModbusDetail

from utils.common import PROJECT_PATH, FRONTEND_PATH


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

        # Divide window in two sections:
        self.main_window_sections_splitter = QSplitter()

        # Left section:
        self.project_structure_section = ProjectStructureSection()
        self.project_structure_section.tree_view.selectionModel().selectionChanged.connect(self.set_detail_section)

        # Right section:
        self.detail_section = self.set_detail_section()

        # Add sections to splitter
        self.main_window_sections_splitter.addWidget(self.project_structure_section)
        self.main_window_sections_splitter.addWidget(self.detail_section)

        # Main layout:
        self.main_window_layout = QVBoxLayout()
        self.main_window_layout.addWidget(self.main_window_sections_splitter)

        # Configurar el widget central
        container = QWidget()
        container.setLayout(self.main_window_layout)
        self.setCentralWidget(container)

    def set_detail_section(self):
        item = self.project_structure_section.get_selected_item()

        if item is not None and item.parent() is not None:  # Check if it is not the root
            item_dataclass = item.data(Qt.ItemDataRole.UserRole)
            if item_dataclass.type == "Modbus":
                self.detail_section = ModbusDetail(item_dataclass)
            else:
                self.detail_section = QLabel("Not implemented yet")
                self.detail_section.setMinimumSize(500, 600)
        else:
            self.detail_section = QLabel("Select an item to display information")
            self.detail_section.setMinimumSize(500, 600)

        if self.main_window_sections_splitter.count() > 1:
            self.main_window_sections_splitter.replaceWidget(1, self.detail_section)
        return self.detail_section


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme=f"{FRONTEND_PATH}/theme.xml", css_file=f"{FRONTEND_PATH}/styles.css")

    window = MainWindow()
    window.show()

    app.exec()
