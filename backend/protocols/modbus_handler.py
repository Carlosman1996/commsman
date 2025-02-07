import binascii
import time

from pymodbus.client import ModbusTcpClient
from backend.protocols.base_protocol import BaseProtocol


class ModbusHandler(BaseProtocol):
    def __init__(self):
        self.client = None
        self.last_packet_send = None
        self.last_packet_recv = None

    def connect(self, host: str, port: int):
        self.client = ModbusTcpClient(host=host, port=port, trace_packet=self.trace_packet)
        return self.client.connect()

    def trace_packet(self, sending: bool, data: bytes) -> bytes:
        self.last_packet_send = sending
        self.last_packet_recv = data
        return data

    @staticmethod
    def decode_response(func):
        def wrap(*args, **kwargs):
            start_time = time.time()

            try:
                response = func(*args, **kwargs)
                packet_recv = args[0].last_packet_recv
                packet_send = args[0].last_packet_recv

                if response.isError():
                    raise Exception(f"Modbus response returns error: {response}. Packet send: {packet_recv}. Packet received: {packet_recv}")

                byte_count = len(packet_recv)
                transaction_id = int.from_bytes(packet_recv[0:2], byteorder='big')  # Bytes 2 and 3
                protocol_id = int.from_bytes(packet_recv[2:4], byteorder='big')  # Bytes 2 and 3
                unit_id = packet_recv[6]  # Byte 6 (Unit ID in Modbus TCP)
                function_code = packet_recv[7]  # Function code

                response_dict = {
                    "slave_id": unit_id,
                    "transaction_id": transaction_id,
                    "protocol_id": protocol_id,
                    "function_code": function_code,
                    "byte_count": byte_count,
                    "raw_packet_recv": " ".join(f"0x{byte:02X}" for byte in packet_recv),
                    "raw_packet_send": " ".join(f"0x{byte:02X}" for byte in packet_send)
                }

                if "Read" in kwargs.get("function"):
                    response_dict["address"] = kwargs.get("address")
                    response_dict["registers"] = (response.registers or response.bits)[:kwargs.get("count")]
                else:
                    response_dict["address"] = response.address
                    response_dict["registers"] = kwargs.get("values")

            except Exception as e:
                response_dict = {"error_message": e}

            end_time = time.time()
            elapsed_time = end_time - start_time
            request_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

            response_dict["elapsed_time"] = round(elapsed_time * 1000, 3)
            response_dict["timestamp"] = request_timestamp

            return response_dict

        return wrap

    @decode_response
    def execute_request(self, function: str, address: int, count: int, slave: int, values: list = None):

        def check_values():
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
            case "Write Coil":
                check_values()
                return self.client.write_coil(address=address, value=values[0], slave=slave)
            case "Write Coils":
                check_values()
                return self.client.write_coils(address=address, values=values, slave=slave)
            case "Write Register":
                check_values()
                return self.client.write_register(address=address, value=values[0], slave=slave)
            case "Write Registers":
                check_values()
                return self.client.write_registers(address=address, values=values, slave=slave)
            case _:
                raise Exception(f"Function {function} not supported")

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
