from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout,
                             QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QTableWidgetItem, QSplitter)


class IconTextWidget(QWidget):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(75, 75)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(text)
        text_label.setFixedHeight(50)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(20)
        layout.addStretch(1)

        self.setStyleSheet("font-size: 16px; font-weight: bold;")


class CustomGridLayout(QGridLayout):
    def __init__(self, height=30, label_width=150, field_width=200):
        # TODO: all layouts must have this format for reusability and consistency
        super().__init__()
        self.height = height  # Maximum height
        self.label_width = label_width  # Maximum width for labels
        self.field_width = field_width  # Maximum width for fields
        self.table = []  # Store references to rows for visibility control
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def add_widget(self, label, field, column=0, index=None):
        label.setMaximumWidth(self.label_width)
        label.setMinimumWidth(self.label_width)
        label.setMaximumHeight(self.height)

        field.setMaximumWidth(self.field_width)
        field.setMinimumWidth(self.field_width)

        if isinstance(field, CustomTable):
            label.setContentsMargins(0, 5, 0, 0)
            alignment = Qt.AlignmentFlag.AlignTop
        else:
            alignment = None

        # Store the row (label and field) for visibility control
        if column >= len(self.table):
            self.table.append([])
            self.setColumnStretch(len(self.table) - 1, 1)
        if index:
            self.table[column][index] = (label, field)
        else:
            index = len(self.table[column])
            self.table[column].append((label, field))

        # Add the row to the layout
        if alignment:
            super().addWidget(label, index, column * 2, alignment)
            super().addWidget(field, index, (column * 2) + 1, alignment)
        else:
            super().addWidget(label, index, column * 2)
            super().addWidget(field, index, (column * 2) + 1)

    def show_row(self, column, index):
        """Show a specific row by index."""
        label, field = self.table[column][index]
        label.show()
        field.show()

    def hide_row(self, column, index):
        """Hide a specific row by index."""
        label, field = self.table[column][index]
        label.hide()
        field.hide()


class CustomTable(QTableWidget):
    def __init__(self, headers):
        super().__init__()

        self.headers = headers
        self.set_style()

    def set_style(self):
        self.setMaximumWidth(200 * len(self.headers))
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setStyleSheet("""
            QTableWidget {
                border: none; /* Remove any outer border */
            }
            QTableWidget::item:selected {
                background-color: #D5D7D6;
            }
            QToolTip {
                background-color: #D5D7D6;
            }
        """)

    def clear(self):
        super().clear()
        self.set_style()

    def setItem(self, *args, **kwargs):
        super().setItem(*args, **kwargs)
        self.adjust_table_height()

    def insertRow(self, *args, **kwargs):
        super().insertRow(*args, **kwargs)
        self.adjust_table_height()

    def removeRow(self, *args, **kwargs):
        super().removeRow(*args, **kwargs)
        self.adjust_table_height()

    def adjust_table_height(self):
        header_height = self.horizontalHeader().height()
        row_height = self.rowHeight(0) if self.rowCount() > 0 else 30  # Default if no rows

        # Limit height to max_visible_rows
        visible_rows = self.rowCount() + 1

        # Total height = header + visible rows + padding
        total_height = header_height + (row_height * visible_rows) + 4

        self.setMaximumHeight(total_height)

    def set_items(self, items):
        if isinstance(items, list):
            for row, item in enumerate(items):
                self.setItem(row, 0, QTableWidgetItem(str(item)))

    def get_values(self):
        """Read values from the table and print them."""
        row_data = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if not item:
                row_data.append("")
            else:
                try:
                    row_data.append(int(item.text()))
                except:
                    row_data.append(item.text())
        return row_data


class CustomComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_item(self, item):
        # Set item based on class attribute
        if item in [self.itemText(i) for i in range(self.count())]:
            self.setCurrentText(item)
        else:
            self.setCurrentIndex(0)  # Fallback if not found


class CustomGroupBox(QGroupBox):
    def __init__(self, title, information):
        super().__init__(title)

        status_layout = QVBoxLayout()
        self.status_label = QLabel(information)
        status_layout.addWidget(self.status_label)
        self.setLayout(status_layout)
