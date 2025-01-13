from dataclasses import dataclass
from pymodbus.client import ModbusTcpClient
from backend.protocols.base_protocol import BaseProtocol


@dataclass
class ModbusRequest:
    name: str
    client: str
    operation: str
    register_type: str
    slave: int
    address: int
    count: int = 1
    value: int = 0


class ModbusHandler(BaseProtocol):
    def __init__(self, name: str, client: str, host: str, port: int):
        self.name = name
        self.client = client
        self.host = host
        self.port = port
        self.client = None

    def connect(self):
        self.client = ModbusTcpClient(host=self.host, port=self.port)
        return self.client.connect()

    @staticmethod
    def decode_response(func):
        def wrap(*args, **kwargs):
            response = func(*args, **kwargs)
            response_dict = {
                "slave_id": response.dev_id,
                "transaction_id": response.transaction_id,
                "address": response.address,
                "bits": response.bits,
                "registers": response.registers,
            }
            return response_dict
        return wrap

    @decode_response
    def read(self, register_type: str, address: int, count: int, slave: int):
        match register_type:
            case "coil":
                return self.client.read_coils(address=address, count=count, slave=slave)
            case "discrete_input":
                return self.client.read_discrete_inputs(address=address, count=count, slave=slave)
            case "holding_register":
                return self.client.read_holding_registers(address=address, count=count, slave=slave)
            case "input_register":
                return self.client.read_input_registers(address=address, count=count, slave=slave)
            case _:
                raise Exception(f"Modbus read function {register_type} does not exist")

    @decode_response
    def write(self, register_type: str, address: int, value: int, slave: int):
        match register_type:
            case "coil":
                return self.client.write_coil(address=address, value=value, slave=slave)
            case "holding_register":
                return self.client.write_register(address=address, value=value, slave=slave)
            case _:
                raise Exception(f"Modbus write function {register_type} does not exist")

    def disconnect(self):
        if self.client:
            self.client.close()

    def execute_request(self, request: ModbusRequest):
        match request.operation:
            case "read":
                return self.read(register_type=request.register_type,
                                 address=request.address,
                                 count=request.count,
                                 slave=request.slave)
            case "write":
                return self.write(register_type=request.register_type,
                                  address=request.address,
                                  value=request.value,
                                  slave=request.slave)
            case _:
                raise Exception(f"Function {request.operation} does not exist")


if __name__ == "__main__":
    modbus_handler = ModbusHandler(name="client_1",
                                   host="localhost",
                                   port=5020)
    modbus_handler.connect()

    modbus_request = ModbusRequest(name="request_1",
                                   operation="read",
                                   register_type="holding_register",
                                   slave=0,
                                   address=0,
                                   count=6,
                                   client="modbus_client")
    print(modbus_handler.execute_request(modbus_request))

    modbus_handler.disconnect()
