from dataclasses import dataclass, field
from functools import partial


@dataclass
class ModbusTcpClient:
    name: str
    item_type: str = "Modbus"
    client_type: str = "TCP"
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 502


@dataclass
class ModbusRtuClient:
    name: str
    item_type: str = "Modbus"
    client_type: str = "RTU"
    serial_port: str = "COM1"
    serial_baudrate: int = 115200


@dataclass
class ModbusResponse:
    name: str
    item_type: str = "Modbus"
    slave: int = None
    transaction_id: int = None
    protocol_id: int = None
    function_code: int = None
    address: int = None
    registers: list[int] = None
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
    client: ModbusTcpClient = field(default_factory=partial(ModbusTcpClient, "unknown"))
    function: str = "Read Holding Registers"
    data_type: str = "16-bit Integer"
    slave: int = 0
    address: int = 0
    count: int = 1
    values: list = None
    last_response: ModbusResponse = None
