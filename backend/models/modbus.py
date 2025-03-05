from dataclasses import dataclass

from backend.models.base import BaseRequest, BaseResult, Base


@dataclass
class ModbusTcpClient(Base):
    item_type: str = "Modbus"
    client_type: str = "Modbus TCP"
    host: str = "127.0.0.1"
    port: int = 502
    timeout: int = 3
    retries: int = 3


@dataclass
class ModbusRtuClient(Base):
    item_type: str = "Modbus"
    client_type: str = "Modbus RTU"
    com_port: str = "COM1"
    baudrate: int = 9600
    parity: str = "None"
    stopbits: int = 1
    bytesize: int = 8
    timeout: int = 3
    retries: int = 3


@dataclass
class ModbusTcpResponse(BaseResult):
    item_type: str = "Modbus"
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
    item_type: str = "Modbus"
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
class ModbusRequest(BaseRequest):
    item_type: str = "Modbus"
    client_type: str = "Inherit from parent"
    function: str = "Read Holding Registers"
    data_type: str = "16-bit Integer"
    slave: int = 0
    address: int = 0
    count: int = 1
    values: list = None
