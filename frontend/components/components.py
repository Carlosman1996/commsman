from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QStandardItemModel
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QTabWidget, QTextEdit, QGridLayout,
                             QHBoxLayout, QTableWidget, QAbstractItemView, QHeaderView, QGroupBox,
                             QTableWidgetItem, QSplitter, QMessageBox, QFrame, QSizePolicy)


class IconTextWidget(QWidget):
    def __init__(self, text, icon_path, icon_size, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(75, 75)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(icon_size)

        text_label = QLabel(text)
        text_label.setFixedHeight(50)
        text_label.setMinimumWidth(200)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.setSpacing(20)
        layout.addStretch(1)

        self.setStyleSheet("font-size: 16px; font-weight: bold;")


class CustomGridLayout(QGridLayout):

    signal_update_item = pyqtSignal()

    def __init__(self, height=30, label_width=150, field_width=200):
        # TODO: all layouts must have this format for reusability and consistency
        super().__init__()
        self.height = height  # Maximum height
        self.label_width = label_width  # Maximum width for labels
        self.field_width = field_width  # Maximum width for fields
        self.table = []  # Store references to rows for visibility control
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def add_widget(self, label, field, column=0, index=None, connect_signal=True):
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

        if connect_signal:
            self.set_widget_signal(field)

        # Add the row to the layout
        if alignment:
            super().addWidget(label, index, column * 2, alignment)
            super().addWidget(field, index, (column * 2) + 1, alignment)
        else:
            super().addWidget(label, index, column * 2)
            super().addWidget(field, index, (column * 2) + 1)

    def set_widget_signal(self, widget):
        if isinstance(widget, CustomTable):
            widget.itemChanged.connect(self.signal_update_item)
        elif isinstance(widget, CustomComboBox):
            widget.currentTextChanged.connect(self.signal_update_item)
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(self.signal_update_item)
        elif isinstance(widget, QPushButton):
            widget.clicked.connect(self.signal_update_item)
        elif isinstance(widget, QTextEdit) or isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.signal_update_item)
        elif isinstance(widget, QLabel):
            pass
        else:
            raise Exception(f"Widget instance {type(widget)} - {widget} not defined")

    def get_label(self, column, index):
        """Get a specific label by index."""
        label, _ = self.table[column][index]
        return label

    # TODO: get field by key, better than index
    def get_field(self, column, index):
        """Get a specific label by index."""
        _, field = self.table[column][index]
        return field

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

    def clear_layout(self, from_item_row: int):
        """Remove and delete all widgets from a layout."""
        new_table = []
        for index_column, rows in enumerate(self.table):
            for index_row, widgets in enumerate(rows):
                if index_row >= from_item_row:
                    for widget in widgets:
                        widget.deleteLater()
                else:
                    if len(new_table) == index_column:
                        new_table.append([])
                    if len(new_table[index_column]) == index_row:
                        new_table[index_column].append([])
                    new_table[index_column][index_row] = widgets
        self.table = new_table


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
                gridline-color: #E5E5E5;  /* Set the color of table borders */
            }
            QTableWidget::item {
                background-color: #F8F8FF;
            }
            QTableWidget::item:selected {
                background-color: #EFEFEF;
            }
            QToolTip {
                background-color: #EFEFEF;
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


class InfoBox(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QLabel {
                background-color: #F8F8FF;
                border: 2px solid #4F005C;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
                max-height: 25px;
                text-align: center;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
