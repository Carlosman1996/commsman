from dataclasses import dataclass

from frontend.models.base import BaseResult
from frontend.models.run_options import RunOptions


@dataclass
class ModbusTcpClient:
    name: str
    item_type: str = "Modbus"
    host: str = "127.0.0.1"
    port: int = 502
    timeout: int = 3
    retries: int = 3


@dataclass
class ModbusRtuClient:
    name: str
    item_type: str = "Modbus"
    port: str = "COM1"
    baudrate: int = 9600
    parity: str = "None"
    stopbits: int = 1
    bytesize: int = 8
    timeout: int = 3
    retries: int = 3


@dataclass
class ModbusTcpResponse(BaseResult):
    name: str
    item_type: str = "Modbus"
    parent: object = None
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""
    client_type: str = "Modbus TCP"
    slave: int = None
    transaction_id: int = None
    protocol_id: int = None
    function_code: int = None
    address: int = None
    registers: list[int] = None
    raw_packet_recv: str = ""
    raw_packet_send: str = ""
    data_type: str = "16-bit Integer"
    byte_count: int = None


@dataclass
class ModbusRtuResponse(BaseResult):
    name: str
    item_type: str = "Modbus"
    parent: object = None
    result: str = None
    elapsed_time: float = None
    timestamp: str = None
    error_message: str = ""
    client_type: str = "Modbus RTU"
    slave: int = None
    function_code: int = None
    address: int = None
    registers: list[int] = None
    crc: int = None
    raw_packet_recv: str = ""
    raw_packet_send: str = ""
    data_type: str = "16-bit Integer"
    byte_count: int = None


@dataclass
class ModbusRequest:
    name: str
    item_type: str = "Modbus"
    client_type: str = "Inherit from parent"
    client: ModbusTcpClient | ModbusRtuClient = None
    function: str = "Read Holding Registers"
    data_type: str = "16-bit Integer"
    slave: int = 0
    address: int = 0
    count: int = 1
    values: list = None
    last_result: ModbusTcpResponse | ModbusRtuResponse = None
    run_options: RunOptions = None
