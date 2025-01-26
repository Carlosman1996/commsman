import sys
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

from frontend.project_structure_section import ProjectStructureSection
# from qt_material import apply_stylesheet

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

        # Divide window in two sections:
        main_window_sections_splitter = QSplitter()

        # Right section:
        right_section_widget = QLabel("Right section: This is a label")

        # Add sections to splitter
        main_window_sections_splitter.addWidget(ProjectStructureSection())
        main_window_sections_splitter.addWidget(right_section_widget)

        # Main layout:
        main_window_layout = QVBoxLayout()
        main_window_layout.addWidget(main_window_sections_splitter)

        # Configurar el widget central
        container = QWidget()
        container.setLayout(main_window_layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # apply_stylesheet(app, theme="light_teal.xml", css_file=f"{FRONTEND_PATH}/styles.css")

    window = MainWindow()
    window.show()

    app.exec()
