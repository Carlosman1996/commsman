import struct
import time

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.framer import FramerSocket
from pymodbus.pdu import DecodePDU
from backend.base_client import BaseClient


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
            raise Exception(f"Data type '{data_type}' not supported")

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
                raise Exception(f"Data type '{data_type}' not supported")
        except Exception as e:
            address_values[f"{new_address}"] = [f"❗ Decode Error: {e}"]

        index += 1

    return address_values


class CustomFramer(FramerSocket):
    def __init__(self):
        super().__init__(DecodePDU(False))

        self.last_packet_send = b''
        self.last_packet_recv = b''

    def reset_packets(self):
        self.last_packet_send = b''
        self.last_packet_recv = b''

    def buildFrame(self, *args, **kwargs):
        output = super().buildFrame(*args, **kwargs)
        self.last_packet_send = output
        return output

    def processIncomingFrame(self, *args, **kwargs):
        self.last_packet_recv = args[0]
        output = super().processIncomingFrame(*args, **kwargs)
        return output


class CustomModbusTcpClient(BaseClient):
    def __init__(self, host: str, port: int):
        self.client = ModbusTcpClient(host=host, port=port)
        self.framer = CustomFramer()
        self.client.transaction.framer = self.framer

    def connect(self):
        return self.client.connect()

    def execute_modbus_request(self, function: str, address: int, count: int, slave: int, values: list = None):
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
                raise Exception(f"Function '{function}' not supported")

    def execute_request(self, data_type: str, function: str, address: int, count: int, slave: int, values: list = None):
        start_time = time.time()

        self.framer.reset_packets()

        response = "Fatal error"
        response_dict = {}
        try:
            if "Write" in function:
                values = convert_value_before_sending(data_type, values)
            else:
                values = convert_value_before_sending(data_type, [0 for _ in range(count)])
            count = len(values)

            response = self.execute_modbus_request(
                function=function,
                slave=slave,
                address=address,
                count=count,
                values=values)

            response_dict["raw_packet_send"] = " ".join(f"0x{byte:02X}" for byte in self.framer.last_packet_send)
            response_dict["raw_packet_recv"] = " ".join(f"0x{byte:02X}" for byte in self.framer.last_packet_recv)

            response_dict["data_type"] = data_type
            response_dict["slave"] = self.framer.last_packet_recv[6]
            response_dict["transaction_id"] = int.from_bytes(self.framer.last_packet_recv[0:2], byteorder='big')
            response_dict["protocol_id"] = int.from_bytes(self.framer.last_packet_recv[2:4], byteorder='big')
            response_dict["function_code"] = self.framer.last_packet_recv[7]
            response_dict["byte_count"] = len(self.framer.last_packet_recv)
            response_dict["address"] = response.address or address  # TODO: read RAW in read registers
            response_dict["registers"] = response.registers or response.bits or values  # TODO: read RAW in write multiple registers

            if response.isError():
                raise ModbusException("Modbus returns error function code")
        except ModbusException as e:
            response_dict["error_message"] = f"Modbus Client returns response: {response}.\n\nException received: {e}"
        except Exception as e:

            response_dict["error_message"] = f"Exception received: {e}"

        end_time = time.time()
        elapsed_time = end_time - start_time
        request_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

        response_dict["elapsed_time"] = round(elapsed_time * 1000, 3)
        response_dict["timestamp"] = request_timestamp

        return response_dict

    def disconnect(self):
        if self.client:
            self.client.close()


if __name__ == "__main__":
    modbus_handler = CustomModbusTcpClient(host="localhost", port=5020)
    modbus_handler.connect()

    result = modbus_handler.execute_request(
        data_type="16-bit Integer",
        function="Read Holding Registers",
        slave=1,
        address=999,
        count=2,
        values=[1, 0]
    )
    print(result)

    modbus_handler.disconnect()
