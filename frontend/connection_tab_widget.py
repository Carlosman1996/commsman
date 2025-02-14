from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QSpinBox)

from frontend.components.components import CustomGridLayout, CustomComboBox
from frontend.models.modbus import ModbusRtuClient, ModbusTcpClient


class ConnectionTabWidget(QWidget):
    def __init__(self, model, connection_types):
        super().__init__()

        self.model = model
        self.item = self.model.get_selected_item()

        self.grid_layout = CustomGridLayout()

        self.connection_type_combo = CustomComboBox()
        self.connection_type_combo.addItems(connection_types)
        self.grid_layout.add_widget(QLabel("Connection Type:"), self.connection_type_combo, connect_signal=False)

        self.setLayout(self.grid_layout)

        # Set initial state and connect signals:
        try:
            self.update_connection_type(client_type=self.item.client_type, client=self.item.client)
        except Exception as e:
            # TODO: add logger
            print(f"Exception at Connection: {e}")
            self.update_connection_type()

        self.connection_type_combo.currentTextChanged.connect(self.update_connection_type)
        self.grid_layout.signal_update_item.connect(self.update_item)

    def update_connection_type(self, client_type: str = None, client: ModbusRtuClient | ModbusTcpClient = None):
        if client_type is None:
            client_type = self.connection_type_combo.currentText()

        index = self.connection_type_combo.findText(client_type)
        self.connection_type_combo.setCurrentIndex(index)

        self.grid_layout.clear_layout(from_item_row=1)

        if client_type == "No connection":
            pass
        elif client_type == "Modbus TCP":
            if not client:
                client = ModbusTcpClient(
                    name=self.item.name
                )

            host_line_edit = QLineEdit(client.host)
            self.grid_layout.add_widget(QLabel("Host:"), host_line_edit)

            port_spinbox = QSpinBox()
            port_spinbox.setRange(1, 65535)
            port_spinbox.setValue(client.port)
            self.grid_layout.add_widget(QLabel("Port:"), port_spinbox)

            timeout_spinbox = QSpinBox()
            timeout_spinbox.setRange(1, 65535)
            timeout_spinbox.setValue(client.timeout)
            self.grid_layout.add_widget(QLabel("Timeout:"), timeout_spinbox)

            retries_spinbox = QSpinBox()
            retries_spinbox.setRange(1, 65535)
            retries_spinbox.setValue(client.retries)
            self.grid_layout.add_widget(QLabel("Timeout:"), retries_spinbox)
        elif client_type == "Modbus RTU":
            if not client:
                client = ModbusRtuClient(
                    name=self.item.name
                )

            port_line_edit = QLineEdit(client.port)
            self.grid_layout.add_widget(QLabel("Port:"), port_line_edit)

            baudrate_combo = CustomComboBox()
            baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
            index = baudrate_combo.findText(str(client.baudrate))
            baudrate_combo.setCurrentIndex(index)
            self.grid_layout.add_widget(QLabel("Baudrate:"), baudrate_combo)

            parity_combo = CustomComboBox()
            parity_combo.addItems(["None", "Even", "Odd"])
            index = parity_combo.findText(str(client.parity))
            parity_combo.setCurrentIndex(index)
            self.grid_layout.add_widget(QLabel("Parity:"), parity_combo)

            stopbits_spinbox = QSpinBox()
            stopbits_spinbox.setRange(0, 2)
            stopbits_spinbox.setValue(client.stopbits)
            self.grid_layout.add_widget(QLabel("Stopbits:"), stopbits_spinbox)

            bytesize_spinbox = QSpinBox()
            bytesize_spinbox.setRange(7, 8)
            bytesize_spinbox.setValue(client.bytesize)
            self.grid_layout.add_widget(QLabel("Bytesize:"), bytesize_spinbox)

            timeout_spinbox = QSpinBox()
            timeout_spinbox.setRange(1, 65535)
            timeout_spinbox.setValue(client.timeout)
            self.grid_layout.add_widget(QLabel("Timeout:"), timeout_spinbox)

            retries_spinbox = QSpinBox()
            retries_spinbox.setRange(1, 65535)
            retries_spinbox.setValue(client.retries)
            self.grid_layout.add_widget(QLabel("Retries:"), retries_spinbox)
        else:
            raise Exception(f"Connection type {client_type} not allowed")

        self.update_item()

    def update_item(self):
        client_type = self.connection_type_combo.currentText()
        if client_type == "No connection":
            client = None
        elif client_type == "Modbus TCP":
            client = ModbusTcpClient(
                name=self.item.name,
                host=self.grid_layout.get_field(0, 1).text(),
                port=int(self.grid_layout.get_field(0, 2).text()),
                timeout=int(self.grid_layout.get_field(0, 3).text()),
                retries=int(self.grid_layout.get_field(0, 4).text())
            )
        elif client_type == "Modbus RTU":
            client = ModbusRtuClient(
                name=self.item.name,
                port=self.grid_layout.get_field(0, 1).text(),
                baudrate=int(self.grid_layout.get_field(0, 2).currentText()),
                parity=self.grid_layout.get_field(0, 3).currentText(),
                stopbits=int(self.grid_layout.get_field(0, 4).text()),
                bytesize=int(self.grid_layout.get_field(0, 5).text()),
                timeout=int(self.grid_layout.get_field(0, 6).text()),
                retries=int(self.grid_layout.get_field(0, 7).text())
            )
        else:
            raise Exception(f"Connection type {client_type} not allowed")

        self.model.update_item(client_type=client_type, client=client)
