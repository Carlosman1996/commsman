from dataclasses import dataclass, field
from functools import partial


@dataclass
class ModbusClient:
    name: str
    item_type: str = "Modbus"
    client_type: str = "TCP"
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 502
    serial_port: str = "COM1"
    serial_baudrate: int = 115200

    def __setattr__(self, key, value):
        if key == "item_type" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "client_type" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type ModbusClient. Current value is {value}")
        if key == "tcp_host" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "tcp_port" and not isinstance(value, int):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "serial_port" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type int. Current value is {value}")
        if key == "serial_baudrate" and not isinstance(value, int):
            raise ValueError(f"Key {key} has type int. Current value is {value}")

        super().__setattr__(key, value)


@dataclass
class ModbusResponse:
    name: str
    item_type: str = "Modbus"
    slave: int = None
    transaction_id: int = None
    protocol_id: int = None
    function_code: int = None
    address: int = None
    registers: list[int] = field(default_factory=list)
    raw_packet_recv: str = ""
    raw_packet_send: str = ""
    elapsed_time: float = None
    timestamp: str = None
    data_type: str = "16-bit Integer"
    byte_count: int = None
    error_message: str = ""


@dataclass
class ModbusRequest:
    name: str
    item_type: str = "Modbus"
    client: ModbusClient = field(default_factory=partial(ModbusClient, "unknown"))
    function: str = "Read Holding Registers"
    data_type: str = "16-bit Integer"
    slave: int = 0
    address: int = 0
    count: int = 1
    values: list = field(default_factory=list)
    last_response: ModbusResponse = None

    def __setattr__(self, key, value):
        if key == "item_type" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "client" and not isinstance(value, ModbusClient):
            raise ValueError(f"Key {key} has type ModbusClient. Current value is {value}")
        if key == "function" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "data_type" and not isinstance(value, str):
            raise ValueError(f"Key {key} has type str. Current value is {value}")
        if key == "slave" and not isinstance(value, int):
            raise ValueError(f"Key {key} has type int. Current value is {value}")
        if key == "address" and not isinstance(value, int):
            raise ValueError(f"Key {key} has type int. Current value is {value}")
        if key == "count" and not isinstance(value, int):
            raise ValueError(f"Key {key} has type int. Current value is {value}")
        if key == "values" and not isinstance(value, list):
            raise ValueError(f"Key {key} has type list. Current value is {value}")

        super().__setattr__(key, value)
