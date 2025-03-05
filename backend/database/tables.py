from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


# Clients Table
class ClientTable(Base):
    __tablename__ = "clients"

    uuid = Column(String, primary_key=True)


# Clients Table (for Modbus TCP and RTU)
class ModbusClientTable(Base):
    __tablename__ = "modbus_clients"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)

    parent_uuid = Column(String, ForeignKey("clients.uuid"), nullable=True)  # Parent Collection
    client_type = Column(String)

    # Only for TCP
    host = Column(String, nullable=True)
    port = Column(Integer, nullable=True)

    # Only for RTU
    com_port = Column(String, nullable=True)
    baudrate = Column(Integer, nullable=True)
    parity = Column(String, nullable=True)
    stopbits = Column(Integer, nullable=True)
    bytesize = Column(Integer, nullable=True)

    timeout = Column(Integer)
    retries = Column(Integer)


# Run Options Table
class RunOptionsTable(Base):
    __tablename__ = "run_options"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)

    polling = Column(Boolean)
    polling_interval = Column(Integer)
    delayed_start = Column(Integer)


# Collections Table
class CollectionTable(Base):
    __tablename__ = "collections"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)
    parent_uuid = Column(String, ForeignKey("collections.uuid"), nullable=True)  # Parent Collection

    client = Column(String, ForeignKey("clients.uuid"), nullable=True)
    client_type = Column(String)
    run_options = Column(String, ForeignKey("run_options.uuid"), nullable=True)
    last_result = Column(String, ForeignKey("collection_results.uuid"), nullable=True)


# Collection Results Table
class CollectionResultsTable(Base):
    __tablename__ = "collection_results"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)

    parent_uuid = Column(String, ForeignKey("collection_results.uuid"), nullable=True)  # Parent Collection
    client_type = Column(String)
    result = Column(String)
    elapsed_time = Column(Float)
    timestamp = Column(String)
    error_message = Column(String, default="")

    total_ok = Column(Integer)
    total_failed = Column(Integer)
    total_pending = Column(Integer)


# Modbus Requests Table
class ModbusRequestTable(Base):
    __tablename__ = "modbus_requests"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)
    parent_uuid = Column(String, ForeignKey("collections.uuid"), nullable=True)  # Parent Collection

    client = Column(String, ForeignKey("clients.uuid"), nullable=True)
    client_type = Column(String)
    run_options = Column(String, ForeignKey("run_options.uuid"), nullable=True)
    last_result = Column(String, ForeignKey("modbus_results.uuid"), nullable=True)

    function = Column(String)
    data_type = Column(String)
    slave = Column(Integer)
    address = Column(Integer)
    count = Column(Integer)
    values = Column(String)   # List


# Collection Results Table
class ModbusResultsTable(Base):
    __tablename__ = "modbus_results"

    uuid = Column(String, primary_key=True)
    name = Column(String)
    item_type = Column(String)
    item_handler = Column(String)

    parent_uuid = Column(String, ForeignKey("collection_results.uuid"), nullable=True)  # Parent Collection
    client_type = Column(String)
    result = Column(String)
    elapsed_time = Column(Float)
    timestamp = Column(String)
    error_message = Column(String, default="")

    slave = Column(Integer, nullable=True)
    transaction_id = Column(Integer, nullable=True)
    protocol_id = Column(Integer, nullable=True)
    function_code = Column(Integer, nullable=True)
    address = Column(Integer, nullable=True)
    registers = Column(String, nullable=True)   # List
    crc = Column(Integer, nullable=True)
    raw_packet_recv = Column(String, default="")
    raw_packet_send = Column(String, default="")
    data_type = Column(String, default="16-bit Integer")
    byte_count = Column(Integer, nullable=True)


# Initialize Database
engine = create_engine("sqlite:///commsman.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
