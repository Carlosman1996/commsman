from functools import partial

from PyQt6.QtWidgets import (QWidget, QLabel,
                             QLineEdit, QSpinBox, QVBoxLayout)

from frontend.base_detail_widget import BaseRequest
from frontend.components.components import CustomGridLayout, CustomComboBox


class ConnectionTabWidget(BaseRequest):

    def __init__(self, model, controller, connection_types):
        super().__init__(model)

        self.model = model
        self.item = self.model.get_selected_item()

        main_layout = QVBoxLayout()

        self.grid_layout = CustomGridLayout()

        self.connection_type_combo = CustomComboBox()
        self.connection_type_combo.addItems(connection_types)
        self.grid_layout.add_widget(QLabel("Connection Type:"), self.connection_type_combo)

        # Add the grid layout to the main layout
        main_layout.addLayout(self.grid_layout)

        self.setLayout(main_layout)

        # Set initial state and connect signals:
        self.update_view(load_data=True)

        self.grid_layout.signal_update_item.connect(partial(self.update_view, load_data=False))

    def update_view(self, load_data: bool = False):
        # TODO: refactor to follow the strategy of run_options widget, for example. Use BaseRequest to update the view when the item changes, not when the view changes
        item_client_type = self.item.client_type
        item_client = self.item.client

        if item_client_type != self.connection_type_combo.currentText():
            if load_data:
                index = self.connection_type_combo.findText(item_client_type)
                self.connection_type_combo.setCurrentIndex(index)
            else:
                # Reset all information related to client due to type has been changed:
                item_client = None
                item_client_type = self.connection_type_combo.currentText()

            self.grid_layout.clear_layout(from_item_row=1)

            if item_client_type == "Modbus TCP":
                if not item_client:
                    item_client = self.model.create_item(item_name=self.item.name,
                                                         item_handler="ModbusTcpClient",
                                                         parent_uuid=self.item.uuid,
                                                         attribute="client")
                    self.item = self.model.get_selected_item()

                host_line_edit = QLineEdit(item_client.host)
                self.grid_layout.add_widget(QLabel("Host:"), host_line_edit)

                port_spinbox = QSpinBox()
                port_spinbox.setRange(1, 65535)
                port_spinbox.setValue(item_client.port)
                self.grid_layout.add_widget(QLabel("Port:"), port_spinbox)

                timeout_spinbox = QSpinBox()
                timeout_spinbox.setRange(1, 65535)
                timeout_spinbox.setValue(item_client.timeout)
                self.grid_layout.add_widget(QLabel("Timeout:"), timeout_spinbox)

                retries_spinbox = QSpinBox()
                retries_spinbox.setRange(1, 65535)
                retries_spinbox.setValue(item_client.retries)
                self.grid_layout.add_widget(QLabel("Timeout:"), retries_spinbox)
            elif item_client_type == "Modbus RTU":
                if not item_client:
                    item_client = self.model.create_item(item_name=self.item.name,
                                                         item_handler="ModbusRtuClient",
                                                         parent_uuid=self.item.uuid,
                                                         attribute="client")
                    self.item = self.model.get_selected_item()


                port_line_edit = QLineEdit(item_client.port)
                self.grid_layout.add_widget(QLabel("Port:"), port_line_edit)

                baudrate_combo = CustomComboBox()
                baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
                index = baudrate_combo.findText(str(item_client.baudrate))
                baudrate_combo.setCurrentIndex(index)
                self.grid_layout.add_widget(QLabel("Baudrate:"), baudrate_combo)

                parity_combo = CustomComboBox()
                parity_combo.addItems(["None", "Even", "Odd"])
                index = parity_combo.findText(str(item_client.parity))
                parity_combo.setCurrentIndex(index)
                self.grid_layout.add_widget(QLabel("Parity:"), parity_combo)

                stopbits_spinbox = QSpinBox()
                stopbits_spinbox.setRange(0, 2)
                stopbits_spinbox.setValue(item_client.stopbits)
                self.grid_layout.add_widget(QLabel("Stopbits:"), stopbits_spinbox)

                bytesize_spinbox = QSpinBox()
                bytesize_spinbox.setRange(7, 8)
                bytesize_spinbox.setValue(item_client.bytesize)
                self.grid_layout.add_widget(QLabel("Bytesize:"), bytesize_spinbox)

                timeout_spinbox = QSpinBox()
                timeout_spinbox.setRange(1, 65535)
                timeout_spinbox.setValue(item_client.timeout)
                self.grid_layout.add_widget(QLabel("Timeout:"), timeout_spinbox)

                retries_spinbox = QSpinBox()
                retries_spinbox.setRange(1, 65535)
                retries_spinbox.setValue(item_client.retries)
                self.grid_layout.add_widget(QLabel("Retries:"), retries_spinbox)

        self.update_item()

    def update_item(self):
        client_type = self.connection_type_combo.currentText()
        if client_type == "Modbus TCP":
            client = {
                "name": self.item.name,
                "host": self.grid_layout.get_field(0, 1).text(),
                "port": int(self.grid_layout.get_field(0, 2).text()),
                "timeout": int(self.grid_layout.get_field(0, 3).text()),
                "retries": int(self.grid_layout.get_field(0, 4).text()),
            }
        elif client_type == "Modbus RTU":
            client = {
                "name": self.item.name,
                "port": self.grid_layout.get_field(0, 1).text(),
                "baudrate": int(self.grid_layout.get_field(0, 2).currentText()),
                "parity": self.grid_layout.get_field(0, 3).currentText(),
                "stopbits": int(self.grid_layout.get_field(0, 4).text()),
                "bytesize": int(self.grid_layout.get_field(0, 5).text()),
                "timeout": int(self.grid_layout.get_field(0, 6).text()),
                "retries": int(self.grid_layout.get_field(0, 7).text()),
            }
        else:
            client = None

        if client:
            self.model.update_item(item_uuid=self.item.client.uuid, **client)
        self.model.update_item(item_uuid=self.item.uuid, client_type=client_type)
