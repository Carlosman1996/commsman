import struct
import time
from abc import abstractmethod
from datetime import timezone, datetime
import tzlocal

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.framer import FramerSocket, FramerRTU
from pymodbus.pdu import DecodePDU
from backend.handlers.base_handler import BaseHandler
from backend.models.modbus import ModbusResponse


class CustomModbusHandler(BaseHandler):
    def __init__(self, client_type: str, **kwargs):
        self.client = None
        self.client_type = client_type
        self.framer = None
        self.response = None

    def connect(self):
        return self.client.connect()

    @staticmethod
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

    def execute_request(self, name: str, item_id: int, parent_result_id: int, data_type: str, function: str, address: int, count: int, slave: int, values: list = None, **kwargs):
        self.framer.reset_packets()
        self.initialize_response_dataclass(name=name, request_id=item_id, parent_result_id=parent_result_id)

        start_time = time.time()
        self.response.result = "Failed"
        self.response.client_type = self.client_type

        try:
            if "Write" in function:
                values = self.convert_value_before_sending(data_type, values)
            else:
                values = self.convert_value_before_sending(data_type, [0 for _ in range(count)])
            count = len(values)

            modbus_response = self.execute_modbus_request(function=function,
                                                          slave=slave,
                                                          address=address,
                                                          count=count,
                                                          values=values)

            self.response.raw_packet_send = " ".join(f"0x{byte:02X}" for byte in self.framer.last_packet_send)
            self.response.raw_packet_recv = " ".join(f"0x{byte:02X}" for byte in self.framer.last_packet_recv)

            self.process_response_data(modbus_response=modbus_response,
                                       address=address,
                                       values=values)

            if modbus_response.isError():
                raise ModbusException("Modbus returns error function code")
            else:
                self.response.result = "OK"
        except ModbusException as e:
            self.response.error_message = f"Modbus Client returns exception:\n\n{e}"
        except Exception as e:
            self.response.error_message = f"Exception received: {e}"

        self.response.data_type = data_type
        end_time = time.time()
        self.response.elapsed_time = end_time - start_time

        return self.response

    def initialize_response_dataclass(self, name: str, request_id: int, parent_result_id: int) -> ModbusResponse:
        self.response = ModbusResponse(
            name=name,
            client_type=self.client_type,
            request_id=request_id,
            parent_id=parent_result_id,
            result="Pending",
            timestamp=datetime.now(tzlocal.get_localzone()),
            elapsed_time=0,
            error_message=""
        )
        return self.response

    @abstractmethod
    def process_response_data(self, modbus_response, address: int, values: list[int]):
        pass

    def disconnect(self):
        if self.client:
            self.client.close()

    def is_connected(self) -> bool:
        return self.client.is_socket_open()


class CustomSocketFramer(FramerSocket):
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


class CustomModbusTcpClient(CustomModbusHandler):
    def __init__(self, host: str, port: int, timeout: int, retries: int, client_type: str, **kwargs):
        super().__init__(client_type)
        self.client = ModbusTcpClient(host=host,
                                      port=port,
                                      timeout=timeout,
                                      retries=retries)
        self.framer = CustomSocketFramer()
        self.client.transaction.framer = self.framer

    def process_response_data(self, modbus_response, address: int, values: list[int]):
        self.response.slave = self.framer.last_packet_recv[6]
        self.response.transaction_id = int.from_bytes(self.framer.last_packet_recv[0:2], byteorder='big')
        self.response.protocol_id = int.from_bytes(self.framer.last_packet_recv[2:4], byteorder='big')
        self.response.function_code = self.framer.last_packet_recv[7]
        self.response.byte_count = len(self.framer.last_packet_recv)
        self.response.address = modbus_response.address or address  # TODO: read RAW in read registers
        self.response.registers = modbus_response.registers or modbus_response.bits or values  # TODO: read RAW in write multiple registers


class CustomRtuFramer(FramerRTU):
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


class CustomModbusRtuClient(CustomModbusHandler):
    def __init__(self, com_port: str, baudrate: int, parity: str, stopbits: int, bytesize: int, timeout: int, retries: int, client_type: str, **kwargs):
        super().__init__(client_type)
        parity = "N" if parity == "None" else parity
        parity = "E" if parity == "Even" else parity
        parity = "O" if parity == "Odd" else parity

        self.client = ModbusSerialClient(port=com_port,
                                         baudrate=baudrate,
                                         parity=parity,
                                         stopbits=stopbits,
                                         bytesize=bytesize,
                                         timeout=timeout,
                                         retries=retries)
        self.framer = CustomRtuFramer()
        self.client.transaction.framer = self.framer

    def process_response_data(self, modbus_response, address: int, values: list[int]):
        self.response.slave = self.framer.last_packet_recv[0]
        self.response.function_code = self.framer.last_packet_recv[1]
        self.response.byte_count = len(self.framer.last_packet_recv)
        self.response.address = modbus_response.address or address  # TODO: read RAW in read registers
        self.response.registers = modbus_response.registers or modbus_response.bits or values  # TODO: read RAW in write multiple registers

        # Extract CRC (last two bytes in RTU frame)
        crc = self.framer.last_packet_recv[-2:]
        self.response.crc = int.from_bytes(crc, byteorder='little')  # CRC is little-endian


if __name__ == "__main__":
    modbus_handler = CustomModbusRtuClient(port='/dev/pts/3',  # Replace with your serial com_port
                                           baudrate=9600,
                                           parity='N',
                                           stopbits=1,
                                           bytesize=8,
                                           timeout=3,
                                           retries=3)
    modbus_handler.connect()

    result = modbus_handler.execute_request(
        name="DEMO",
        data_type="16-bit Integer",
        function="Read Holding Registers",
        slave=2,
        address=3,
        count=1,
        values=[1]
    )
    print(result)

    modbus_handler.disconnect()
