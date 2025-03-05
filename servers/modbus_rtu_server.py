import logging

from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartSerialServer

# Enable logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Define the data blocks for the server
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [index % 2 for index in range(0, 9)]),  # Discrete Inputs
    co=ModbusSequentialDataBlock(0, [index % 2 for index in range(10, 19)]),  # Coils
    hr=ModbusSequentialDataBlock(0, [index for index in range(20, 29)]),  # Holding Registers
    ir=ModbusSequentialDataBlock(0, [index for index in range(30, 39)])  # Input Registers
)
context = ModbusServerContext(slaves=store, single=True)

# Start the Modbus RTU server
print("Starting Modbus RTU Server...")
StartSerialServer(
    context,
    port='/dev/pts/1',  # Ensure this matches the virtual com_port
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8
)

"""
>> socat -d -d pty,raw,echo=0 pty,raw,echo=0 | tee serial_log.txt
"""
