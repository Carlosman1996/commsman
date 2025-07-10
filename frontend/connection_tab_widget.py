from PyQt6.QtWidgets import (QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.base_detail_widget import BaseRequest
from frontend.components.components import CustomGridLayout, CustomComboBox


class BaseConnectionGrid(BaseRequest):

    def __init__(self, api_client, item, grid_layout):
        super().__init__(api_client, item)

        self.item_client = self.item["client"]

        self.grid_layout = grid_layout

        self.grid_layout.signal_update_item.connect(self.update_item)

    def update_item(self):
        pass

    def update_view(self, data: dict):
        pass


class ModbusTcpConnectionGrid(BaseConnectionGrid):

    def __init__(self, api_client, item, grid_layout):
        super().__init__(api_client, item, grid_layout)

        self.host_line_edit = QLineEdit("")
        self.grid_layout.add_widget(QLabel("Host:"), self.host_line_edit)

        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1, 65535)
        self.grid_layout.add_widget(QLabel("Port:"), self.port_spinbox)

        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 65535)
        self.grid_layout.add_widget(QLabel("Timeout:"), self.timeout_spinbox)

        self.retries_spinbox = QSpinBox()
        self.retries_spinbox.setRange(1, 65535)
        self.grid_layout.add_widget(QLabel("Timeout:"), self.retries_spinbox)

        # Set initial state and connect signals:
        self.update_view(data=self.item_client)

    def update_item(self):
        if self.item_client:
            client = {
                "name": self.item["name"],
                "host": self.host_line_edit.text(),
                "port": int(self.port_spinbox.text()),
                "timeout": int(self.timeout_spinbox.text()),
                "retries": int(self.retries_spinbox.text()),
            }
            self.api_client.update_item_from_handler(
                item_handler=self.item_client["item_handler"],
                item_id=self.item_client["item_id"],
                **client,
                request_id=self.request_id,
                callback=self.update_view,
            )
        else:
            self.api_client.create_client_item(
                item_name=self.item["name"],
                item_handler="ModbusTcpClient",
                parent_item_id=self.item["item_id"],
                callback=self.update_view,
            )

    def update_view(self, data: dict):
        if not data:
            self.update_item()
            return
        else:
            self.item_client = data

        self.grid_layout.blockSignals(True)

        self.host_line_edit.setText(self.item_client["host"])
        self.port_spinbox.setValue(self.item_client["port"])
        self.timeout_spinbox.setValue(self.item_client["timeout"])
        self.retries_spinbox.setValue(self.item_client["retries"])

        self.grid_layout.blockSignals(False)


class ModbusRtuConnectionGrid(BaseConnectionGrid):

    def __init__(self, api_client, item, grid_layout):
        super().__init__(api_client, item, grid_layout)

        self.port_line_edit = QLineEdit("")
        self.grid_layout.add_widget(QLabel("Port:"), self.port_line_edit)

        self.baudrate_combo = CustomComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.grid_layout.add_widget(QLabel("Baudrate:"), self.baudrate_combo)

        self.parity_combo = CustomComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.grid_layout.add_widget(QLabel("Parity:"), self.parity_combo)

        self.stopbits_spinbox = QSpinBox()
        self.stopbits_spinbox.setRange(0, 2)
        self.grid_layout.add_widget(QLabel("Stopbits:"), self.stopbits_spinbox)

        self.bytesize_spinbox = QSpinBox()
        self.bytesize_spinbox.setRange(7, 8)
        self.grid_layout.add_widget(QLabel("Bytesize:"), self.bytesize_spinbox)

        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 65535)
        self.grid_layout.add_widget(QLabel("Timeout:"), self.timeout_spinbox)

        self.retries_spinbox = QSpinBox()
        self.retries_spinbox.setRange(1, 65535)
        self.grid_layout.add_widget(QLabel("Retries:"), self.retries_spinbox)

        # Set initial state and connect signals:
        self.update_view(data=self.item_client)

    def update_item(self):
        if self.item_client:
            client = {
                "name": self.item["name"],
                "com_port": self.port_line_edit.text(),
                "baudrate": int(self.baudrate_combo.currentText()),
                "parity": self.parity_combo.currentText(),
                "stopbits": int(self.stopbits_spinbox.text()),
                "bytesize": int(self.bytesize_spinbox.text()),
                "timeout": int(self.timeout_spinbox.text()),
                "retries": int(self.retries_spinbox.text()),
            }
            self.api_client.update_item_from_handler(
                item_handler=self.item_client["item_handler"],
                item_id=self.item_client["item_id"],
                **client,
                request_id=self.request_id,
                callback=self.update_view,
            )
        else:
            self.api_client.create_client_item(
                item_name=self.item["name"],
                item_handler="ModbusRtuClient",
                parent_item_id=self.item["item_id"],
                request_id=self.request_id,
                callback=self.update_view,
            )

    def update_view(self, data: dict):
        if not data:
            self.update_item()
            return
        else:
            self.item_client = data

        self.grid_layout.blockSignals(True)

        self.port_line_edit.setText(self.item_client["com_port"])
        index = self.baudrate_combo.findText(str(self.item_client["baudrate"]))
        self.baudrate_combo.setCurrentIndex(index)
        index = self.parity_combo.findText(str(self.item_client["parity"]))
        self.parity_combo.setCurrentIndex(index)
        self.stopbits_spinbox.setValue(self.item_client["stopbits"])
        self.bytesize_spinbox.setValue(self.item_client["bytesize"])
        self.timeout_spinbox.setValue(self.item_client["timeout"])
        self.retries_spinbox.setValue(self.item_client["retries"])

        self.grid_layout.blockSignals(False)


class ConnectionTabWidget(BaseRequest):

    def __init__(self, api_client, item, connection_types):
        super().__init__(api_client, item)

        self.current_layout_name = connection_types[0]

        self.main_layout = QVBoxLayout()

        self.grid_layout = CustomGridLayout()
        self.setLayout(self.grid_layout)

        # Common component:
        self.connection_type_combo = CustomComboBox()
        self.connection_type_combo.addItems(connection_types)
        self.grid_layout.add_widget(QLabel("Connection Type:"), self.connection_type_combo)

        # Create components:
        self.connection_grids = {
            "No connection": BaseConnectionGrid,
            "Inherit from parent": BaseConnectionGrid,
            "Modbus TCP": ModbusTcpConnectionGrid,
            "Modbus RTU": ModbusRtuConnectionGrid,
        }
        self.current_connection_grid = self.connection_grids[self.current_layout_name](api_client, item, self.grid_layout)

        # Set initial state and connect signals:
        self.update_view(data=self.item)

        self.grid_layout.signal_update_item.connect(self.update_item)

    def update_item(self):
        new_connection_type = self.connection_type_combo.currentText()
        if self.item["client_type"] != new_connection_type:
            self.api_client.update_item_from_handler(
                item_handler=self.item["item_handler"],
                item_id=self.item["item_id"],
                client_id=None,
                client_type=new_connection_type,
                client=None,
                request_id=self.request_id,
                callback=self.update_view
            )

    def update_view(self, data: dict = None):
        """Switch between GridLayouts when QComboBox changes value."""
        new_connection_type = data["client_type"]
        if new_connection_type == self.current_layout_name:
            return
        else:
            self.item = data

        self.grid_layout.blockSignals(True)

        index = self.connection_type_combo.findText(str(self.item["client_type"]))
        self.connection_type_combo.setCurrentIndex(index)

        # Remove previous layout:
        self.grid_layout.clear_layout(from_item_row=1)
        # Add new layout:
        self.current_connection_grid = self.connection_grids[new_connection_type](self.api_client, self.item, self.grid_layout)

        self.current_layout_name = new_connection_type  # Update current state

        self.grid_layout.blockSignals(False)
