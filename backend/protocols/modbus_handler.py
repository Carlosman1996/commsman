import struct
import time

from pymodbus.client import ModbusTcpClient
from backend.protocols.base_protocol import BaseProtocol


def convert_value_before_sending(data_type: str, values: list):
    registers = []
    for value in values:
        if data_type == "16-bit Integer":
            raw_bytes = struct.pack(">h", int(value))
            registers.extend(struct.unpack(">H", raw_bytes))
        elif data_type == "16-bit Unsigned Integer":
            raw_bytes = struct.pack(">H", int(value))
            registers.extend(struct.unpack(">H", raw_bytes))
        elif data_type == "32-bit Integer":
            raw_bytes = struct.pack(">i", int(value))
            registers.extend(struct.unpack(">HH", raw_bytes))
        elif data_type == "32-bit Unsigned Integer":
            raw_bytes = struct.pack(">I", int(value))
            registers.extend(struct.unpack(">HH", raw_bytes))
        elif data_type == "Hexadecimal":
            value = str(value)
            if len(value) % 4 != 0:
                value = value.zfill(len(value) + (4 - len(value) % 4))  # Ensure 16-bit alignment
            raw_bytes = bytes.fromhex(value)
            registers.extend(struct.unpack(">" + "H" * (len(raw_bytes) // 2), raw_bytes))
        elif data_type == "Float":
            raw_bytes = struct.pack(">f", float(value))
            registers.extend(struct.unpack(">HH", raw_bytes))
        elif data_type == "Double":
            raw_bytes = struct.pack(">d", float(value))
            registers.extend(struct.unpack(">HHHH", raw_bytes))
        elif data_type == "String":
            text_bytes = str(value).encode("utf-8")
            if len(text_bytes) % 2 != 0:
                text_bytes += b"\x00"
            registers.extend(struct.unpack(">" + "H" * (len(text_bytes) // 2), text_bytes))
        else:
            raise Exception("Data type not supported")

    return registers


def convert_value_after_sending(data_type: str, address: int, values: list):
    address_values = {}
    index = 0
    while index < len(values):
        new_address = address + index
        try:
            if data_type == "16-bit Integer":
                raw_bytes = struct.pack(">H", values[index])
                address_values[f"{new_address}"] = struct.unpack(">h", raw_bytes[:2])[0]
            elif data_type == "16-bit Unsigned Integer":
                raw_bytes = struct.pack(">H", values[index])
                address_values[f"{new_address}"] = struct.unpack(">H", raw_bytes[:2])[0]
            elif data_type == "32-bit Integer":
                index += 1
                raw_bytes = struct.pack(">" + "H" * 2, *values[index - 1:index + 1])
                address_values[f"{new_address}-{new_address + 1}"] = struct.unpack(">i", raw_bytes[:4])[0]
            elif data_type == "32-bit Unsigned Integer":
                index += 1
                raw_bytes = struct.pack(">" + "H" * 2, *values[index - 1:index + 1])
                address_values[f"{new_address}-{new_address + 1}"] = struct.unpack(">I", raw_bytes[:4])[0]
            elif data_type == "Hexadecimal":
                address_values[f"{new_address}"] = hex(values[index])[2:].zfill(4).upper()
            elif data_type == "Float":
                index += 1
                raw_bytes = struct.pack(">" + "H" * 2, *values[index - 1:index + 1])
                address_values[f"{new_address}-{new_address + 1}"] = struct.unpack(">f", raw_bytes)[0]
            elif data_type == "Double":
                index += 3
                raw_bytes = struct.pack(">" + "H" * 4, *values[index - 3:index + 1])
                address_values[f"{new_address}-{new_address + 3}"] = struct.unpack(">d", raw_bytes)[0]
            elif data_type == "String":
                raw_bytes = struct.pack(">H", values[index])
                address_values[f"{new_address}"] = raw_bytes.decode("utf-8").rstrip("\x00")
            else:
                raise Exception("Data type not supported")
        except Exception as e:
            address_values[f"{new_address}"] = [f"❗ Decode Error: {e}"]

        index += 1

    return address_values


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

            packet_recv = ""
            packet_send = ""
            try:
                if "Write" in kwargs["function"]:
                    kwargs["values"] = convert_value_before_sending(kwargs["data_type"], kwargs["values"])
                else:
                    kwargs["values"] = convert_value_before_sending(kwargs["data_type"], [0 for _ in range(kwargs["count"])])
                kwargs["count"] = len(kwargs["values"])

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
                    "slave": unit_id,
                    "transaction_id": transaction_id,
                    "protocol_id": protocol_id,
                    "function_code": function_code,
                    "byte_count": byte_count,
                    "address": response.address or kwargs.get("address"),
                    "registers": response.registers or response.bits or kwargs["values"],    # TODO: read RAW
                    "data_type": kwargs["data_type"]
                }

            except Exception as e:
                response_dict = {"error_message": e}

            response_dict["raw_packet_recv"] = " ".join(f"0x{byte:02X}" for byte in packet_recv)
            response_dict["raw_packet_send"] = " ".join(f"0x{byte:02X}" for byte in packet_send)

            end_time = time.time()
            elapsed_time = end_time - start_time
            request_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

            response_dict["elapsed_time"] = round(elapsed_time * 1000, 3)
            response_dict["timestamp"] = request_timestamp

            return response_dict

        return wrap

    @decode_response
    def execute_request(self, data_type: str, function: str, address: int, count: int, slave: int, values: list = None):
        self.last_packet_send = None
        self.last_packet_recv = None

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
                if len(values) > 1:
                    raise Exception(f"Only one register can be written. Send {len(values)}. Please, ensure data type selected writes 16 bits")
                return self.client.write_coil(address=address, value=values[0], slave=slave)
            case "Write Coils":
                return self.client.write_coils(address=address, values=values, slave=slave)
            case "Write Register":
                if len(values) > 1:
                    raise Exception(f"Only one register can be written. Send {len(values)}. Please, ensure data type selected writes 16 bits")
                return self.client.write_register(address=address, value=values[0], slave=slave)
            case "Write Registers":
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
