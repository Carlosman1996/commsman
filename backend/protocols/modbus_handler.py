from pymodbus.client import ModbusTcpClient
from backend.protocols.base_protocol import BaseProtocol


class ModbusHandler(BaseProtocol):
    def __init__(self):
        self.client = None

    def connect(self, host: str, port: int):
        self.client = ModbusTcpClient(host=host, port=port)
        return self.client.connect()

    @staticmethod
    def decode_response(func):
        def wrap(*args, **kwargs):
            try:
                response = func(*args, **kwargs)

                if response.isError():
                    raise Exception(f"Modbus response returns error: {response}")

                if "Read" in kwargs.get("function"):
                    response_dict = {
                        "slave_id": response.dev_id,
                        "transaction_id": response.transaction_id,
                        "address": kwargs.get("address"),
                        "registers": (response.registers or response.bits)[:kwargs.get("count")],
                    }
                else:
                    response_dict = {
                        "slave_id": response.dev_id,
                        "transaction_id": response.transaction_id,
                        "address": response.address,
                        "registers": kwargs.get("values"),
                    }
                return response_dict
            except Exception as e:
                return {"error_message": e}
        return wrap

    @decode_response
    def execute_request(self, function: str, address: int, count: int, slave: int, values: list = None):

        # Validate values:
        if any(not isinstance(value, int) for value in values):
            raise ValueError("Values to write have incorrect format")

        match function:
            case "Read Coils":
                return self.client.read_coils(address=address, count=count, slave=slave)
            case "Read Discrete Inputs":
                return self.client.read_discrete_inputs(address=address, count=count, slave=slave)
            case "Read Holding Registers":
                return self.client.read_holding_registers(address=address, count=count, slave=slave)
            case "Read Input Registers":
                return self.client.read_input_registers(address=address, count=count, slave=slave)
            case "Write Coils":
                return self.client.write_coils(address=address, values=values, slave=slave)
            case "Write Registers":
                return self.client.write_registers(address=address, values=values, slave=slave)
            case _:
                raise Exception(f"Function {function} does not exist")

    def disconnect(self):
        if self.client:
            self.client.close()


if __name__ == "__main__":
    modbus_handler = ModbusHandler()
    modbus_handler.connect(host="localhost",
                           port=5020)

    result = modbus_handler.execute_request(function="Write Coils",
                                            slave=1,
                                            address=1,
                                            count=2,
                                            values=[1, 0])
    print(result)

    result = modbus_handler.execute_request(function="Read Coils",
                                            slave=1,
                                            address=1,
                                            count=2)
    print(result)

    modbus_handler.disconnect()
