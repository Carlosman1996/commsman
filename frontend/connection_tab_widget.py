from PyQt6.QtWidgets import (QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.base_detail_widget import BaseRequest
from frontend.components.components import CustomGridLayout, CustomComboBox


class BaseConnectionGrid(BaseRequest):

    def __init__(self, repository, grid_layout):
        super().__init__(repository)

        self.grid_layout = grid_layout

        self.repository = repository
        self.item = repository.get_selected_item()

    def update_item(self):
        pass

    def update_view(self, load_data: bool = False):
        pass


class ModbusTcpConnectionGrid(BaseConnectionGrid):

    def __init__(self, repository, grid_layout):
        super().__init__(repository, grid_layout)

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
        self.update_view(load_data=True)

    def update_item(self):
        if self.item.client:
            client = {
                "name": self.item.name,
                "host": self.host_line_edit.text(),
                "com_port": int(self.port_spinbox.text()),
                "timeout": int(self.timeout_spinbox.text()),
                "retries": int(self.retries_spinbox.text()),
            }
            self.repository.update_item(item_uuid=self.item.client.uuid, **client)
        else:
            self.repository.create_item(item_name=self.item.name,
                                   item_handler="ModbusTcpClient",
                                   parent_uuid=self.item.uuid,
                                   attribute="client")

    def update_view(self, load_data: bool = False):
        if load_data and not self.item.client:
            self.update_sequence()

        self.host_line_edit.setText(self.item.client.host)
        self.port_spinbox.setValue(self.item.client.port)
        self.timeout_spinbox.setValue(self.item.client.timeout)
        self.retries_spinbox.setValue(self.item.client.retries)


class ModbusRtuConnectionGrid(BaseConnectionGrid):

    def __init__(self, repository, grid_layout):
        super().__init__(repository, grid_layout)

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
        self.update_view(load_data=True)

    def update_item(self):
        if self.item.client:
            client = {
                "name": self.item.name,
                "com_port": self.port_line_edit.text(),
                "baudrate": int(self.baudrate_combo.currentText()),
                "parity": self.parity_combo.currentText(),
                "stopbits": int(self.stopbits_spinbox.text()),
                "bytesize": int(self.bytesize_spinbox.text()),
                "timeout": int(self.timeout_spinbox.text()),
                "retries": int(self.retries_spinbox.text()),
            }
            self.repository.update_item(item_uuid=self.item.client.uuid, **client)
        else:
            self.repository.create_item(item_name=self.item.name,
                                   item_handler="ModbusRtuClient",
                                   parent_uuid=self.item.uuid,
                                   attribute="client")

    def update_view(self, load_data: bool = False):
        if load_data and not self.item.client:
            self.update_sequence()

        self.port_line_edit.setText(self.item.client.com_port)
        index = self.baudrate_combo.findText(str(self.item.client.baudrate))
        self.baudrate_combo.setCurrentIndex(index)
        index = self.parity_combo.findText(str(self.item.client.parity))
        self.parity_combo.setCurrentIndex(index)
        self.stopbits_spinbox.setValue(self.item.client.stopbits)
        self.bytesize_spinbox.setValue(self.item.client.bytesize)
        self.timeout_spinbox.setValue(self.item.client.timeout)
        self.retries_spinbox.setValue(self.item.client.retries)


class ConnectionTabWidget(BaseRequest):

    def __init__(self, repository, connection_types):
        super().__init__(repository)

        self.repository = repository
        self.item = self.repository.get_selected_item()
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
        self.current_connection_grid = self.connection_grids[self.current_layout_name](self.repository, self.grid_layout)

        # Set initial state and connect signals:
        self.update_view(load_data=True)

        self.grid_layout.signal_update_item.connect(self.update_sequence)

    def update_item(self):
        new_connection_grid = self.connection_type_combo.currentText()
        if self.item.client_type == new_connection_grid:
            self.current_connection_grid.update_item()
        else:
            self.repository.update_item(item_uuid=self.item.uuid, client=None, client_type=new_connection_grid)

    def update_view(self, load_data: bool = False):
        """Switch between GridLayouts when QComboBox changes value."""

        new_connection_grid = self.item.client_type
        if not load_data and new_connection_grid == self.current_layout_name:
            self.current_connection_grid.update_view()
            return

        self.grid_layout.blockSignals(True)

        index = self.connection_type_combo.findText(str(self.item.client_type))
        self.connection_type_combo.setCurrentIndex(index)

        # Remove previous layout:
        self.grid_layout.clear_layout(from_item_row=1)
        # Add new layout:
        self.current_connection_grid = self.connection_grids[new_connection_grid](self.repository, self.grid_layout)

        self.current_layout_name = new_connection_grid  # Update current state

        self.grid_layout.blockSignals(False)
