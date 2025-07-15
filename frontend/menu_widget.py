import os

import markdown
from PyQt6.QtWidgets import QMessageBox, QDialog, QScrollArea, QWidget, QVBoxLayout, QSizePolicy, QTextBrowser

from config import PROJECT_PATH, APP_NAME, VERSION, AUTHOR


class AppInfo:
    def __init__(self):
        self.root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _create_document_dialog(self, title, content, parent, is_markdown=False):
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.resize(800, 600)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)

        browser = QTextBrowser()
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if is_markdown:
            browser.setHtml(self._convert_markdown(content))
        else:
            browser.setPlainText(content)
            browser.setFontFamily("Courier New")

        layout.addWidget(browser)
        scroll.setWidget(container)

        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(scroll)

        return dialog

    def _convert_markdown(self, text):
        html = markdown.markdown(text)
        return f"""
        <html>
        <style>
            body {{ font-family: Arial; line-height: 1.6; padding: 10px; }}
            h1 {{ color: #2c3e50; }}
            code {{ background: #f0f0f0; padding: 2px 4px; }}
            pre {{ background: #f8f8f8; padding: 10px; }}
        </style>
        <body>{html}</body>
        </html>
        """

    def load_file(self, filename):
        """Attempt to load text file from root directory"""
        file_path = os.path.join(self.root_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            return f"{filename} not found in {self.root_path}"
        except Exception as e:
            return f"Error reading {filename}: {str(e)}"

    def show_about(self, parent):
        """Show about dialog"""
        about_text = f"""
        <b>{APP_NAME}</b><br>
        Version: {VERSION}<br>
        Author: {AUTHOR}<br>
        Copyright © {self.get_copyright_year()}<br>
        """
        QMessageBox.about(parent, "About", about_text)

    def show_license(self, parent):
        """Show license dialog with content from LICENSE file"""
        license_text = self.load_file(os.path.join(PROJECT_PATH, "LICENSE.txt"))
        dialog = self._create_document_dialog("License Information", license_text, parent)
        dialog.exec()

    def show_readme(self, parent):
        """Show README dialog"""
        readme_text = self.load_file(os.path.join(PROJECT_PATH, "README.md"))
        dialog = self._create_document_dialog("Application Information", readme_text, parent, is_markdown=True)
        dialog.exec()

    def get_copyright_year(self):
        """Get current year for copyright notice"""
        from datetime import datetime
        return datetime.now().year
