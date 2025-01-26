from dataclasses import dataclass, field


@dataclass
class ModbusRequest:
    name: str
    type: str = "Modbus"
    client: str = None
    operation: str = "read"
    register_type: str = "coil"
    slave: int = 0
    address: int = 0
    count: int = 1
    value: int = 0
