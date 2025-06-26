from backend.models.base import *


@dataclass
class ModbusTcpClient(BaseItem):
    __tablename__ = "modbus_tcp_client"

    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("client.item_id", ondelete="CASCADE"), default=None)

    item_type: Mapped[int] = mapped_column(String, default="Modbus")
    client_type: Mapped[int] = mapped_column(String, default="Modbus TCP")
    host: Mapped[int] = mapped_column(String, default="127.0.0.1")
    port: Mapped[int] = mapped_column(Integer, default=502)
    timeout: Mapped[int] = mapped_column(Integer, default=3)
    retries: Mapped[int] = mapped_column(Integer, default=3)


@dataclass
class ModbusRtuClient(BaseItem):
    __tablename__ = "modbus_rtu_client"

    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("client.item_id", ondelete="CASCADE"), default=None)

    item_type: Mapped[int] = mapped_column(String, default="Modbus")
    client_type: Mapped[int] = mapped_column(String, default="Modbus RTU")
    com_port: Mapped[int] = mapped_column(String, default="COM1")
    baudrate: Mapped[int] = mapped_column(Integer, default=9600)
    parity: Mapped[int] = mapped_column(String, default="None")
    stopbits: Mapped[int] = mapped_column(Integer, default=1)
    bytesize: Mapped[int] = mapped_column(Integer, default=8)
    timeout: Mapped[int] = mapped_column(Integer, default=3)
    retries: Mapped[int] = mapped_column(Integer, default=3)


@dataclass
class ModbusRequest(BaseRequest):
    __tablename__ = "modbus_request"

    item_response_handler: str = "ModbusResponse"

    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("request.item_id", ondelete="CASCADE"), primary_key=True)

    item_type: Mapped[int] = mapped_column(String, default="Modbus")
    client_type: Mapped[int] = mapped_column(String, default="Inherit from parent")
    function: Mapped[int] = mapped_column(String, default="Read Holding Registers")
    data_type: Mapped[int] = mapped_column(String, default="16-bit Integer")
    slave: Mapped[int] = mapped_column(Integer, default=0)
    address: Mapped[int] = mapped_column(Integer, default=0)
    count: Mapped[int] = mapped_column(Integer, default=1)
    values: Mapped[list] = mapped_column(JSON, default=None, nullable=True)


@dataclass
class ModbusResponse(BaseResult):
    __tablename__ = "modbus_response"

    # Initialize to None but it is non-nullable:
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("modbus_request.item_id", ondelete="SET NULL"), nullable=False, default=None)  # Do not delete on cascade because parent result will show incorrect results

    item_type: Mapped[int] = mapped_column(String, default="Modbus")
    slave: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    transaction_id: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    protocol_id: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    function_code: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    address: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    registers: Mapped[list] = mapped_column(JSON, default=None, nullable=True)
    crc: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
    raw_packet_recv: Mapped[int] = mapped_column(String, default="")
    raw_packet_send: Mapped[int] = mapped_column(String, default="")
    data_type: Mapped[int] = mapped_column(String, default="16-bit Integer")
    byte_count: Mapped[int] = mapped_column(Integer, default=None, nullable=True)
