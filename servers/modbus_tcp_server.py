from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import logging

# Configuración básica de logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def run_modbus_server():
    # Crear un bloque de datos (100 registros de ejemplo, con valores iniciales)
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [index % 2 for index in range(0, 9)]),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [index % 2 for index in range(10, 19)]),  # Coils
        hr=ModbusSequentialDataBlock(0, [index for index in range(20, 29)]),  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [index for index in range(30, 39)])  # Input Registers
    )
    context = ModbusServerContext(slaves=store, single=True)

    # Configuración del dispositivo (opcional)
    identity = ModbusDeviceIdentification()
    identity.VendorName = "MyCompany"
    identity.ProductCode = "ModbusServer"
    identity.ProductName = "Modbus Test Server"
    identity.ModelName = "ModbusServerModel"
    identity.MajorMinorRevision = "1.0"

    # Iniciar servidor en el puerto 5020
    logging.info("Iniciando el servidor MODBUS en el puerto 5020...")
    StartTcpServer(context, identity=identity, address=("localhost", 5020))


if __name__ == "__main__":
    run_modbus_server()
