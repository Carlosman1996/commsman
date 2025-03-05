import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.tables import *

# Load JSON data
with open('project_structure_data.json', 'r') as f:
    data = json.load(f)

# Initialize Database
engine = create_engine("sqlite:///commsman.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


def convert_list_to_string(value_list):
    """
    Convert a list of values into a string where:
    - Strings are wrapped in single quotes.
    - Integers and floats are not wrapped in quotes.
    """
    if value_list:
        result = []
        for item in value_list:
            if isinstance(item, str):
                result.append(f"'{item}'")  # Wrap strings in single quotes
            else:
                result.append(str(item))    # Integers and floats are added as-is
        return ', '.join(result)  # Join with commas
    else:
        return None


for uuid, item in data.items():
    # Migrate Clients
    if item.get('item_handler') in ["ModbusTcpClient", "ModbusRtuClient"]:
        client = ClientTable(uuid=item['uuid'])
        session.add(client)
        modbus_client = ModbusClientTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            parent_uuid=item['uuid'],
            client_type=item['client_type'],
            host=item.get('host'),
            port=item.get('port'),
            com_port=item.get('com_port'),
            baudrate=item.get('baudrate'),
            parity=item.get('parity'),
            stopbits=item.get('stopbits'),
            bytesize=item.get('bytesize'),
            timeout=item['timeout'],
            retries=item['retries']
        )
        session.add(modbus_client)

    # Migrate Run Options
    if item.get('item_handler') in ["RunOptions"]:
        run_options = RunOptionsTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            polling=item['polling'],
            polling_interval=item['polling_interval'],
            delayed_start=item['delayed_start']
        )
        session.add(run_options)

    # Migrate Collections
    if item.get('item_handler') in ["Collection"]:
        collection = CollectionTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            parent_uuid=item.get('parent_uuid'),
            client=item.get('client'),
            client_type=item['client_type'],
            run_options=item.get('run_options'),
            last_result=item.get('last_result')
        )
        session.add(collection)

    # Migrate Collection Results
    if item.get('item_handler') in ["CollectionResult"]:
        collection_result = CollectionResultsTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            parent_uuid=item.get('parent_uuid'),
            client_type=item['client_type'],
            result=item['result'],
            elapsed_time=item['elapsed_time'],
            timestamp=item['timestamp'],
            error_message=item.get('error_message', ''),
            total_ok=item['total_ok'],
            total_failed=item['total_failed'],
            total_pending=item['total_pending']
        )
        session.add(collection_result)

    # Migrate Modbus Requests
    if item.get('item_handler') in ["ModbusRequest"]:
        modbus_request = ModbusRequestTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            parent_uuid=item.get('parent_uuid'),
            client=item.get('client'),
            client_type=item['client_type'],
            run_options=item.get('run_options'),
            last_result=item.get('last_result'),
            function=item['function'],
            data_type=item['data_type'],
            slave=item['slave'],
            address=item['address'],
            count=item['count'],
            values=convert_list_to_string(item['values'])
        )
        session.add(modbus_request)

    # Migrate Modbus Results
    if item.get('item_handler') in ["ModbusTcpResponse", "ModbusRtuResponse"]:
        modbus_result = ModbusResultsTable(
            uuid=item['uuid'],
            name=item['name'],
            item_type=item['item_type'],
            item_handler=item['item_handler'],
            parent_uuid=item.get('parent_uuid'),
            client_type=item['client_type'],
            result=item['result'],
            elapsed_time=item['elapsed_time'],
            timestamp=item['timestamp'],
            error_message=item.get('error_message', ''),
            slave=item.get('slave'),
            transaction_id=item.get('transaction_id'),
            protocol_id=item.get('protocol_id'),
            function_code=item.get('function_code'),
            address=item.get('address'),
            registers=convert_list_to_string(item.get('registers')),
            crc=item.get('crc'),
            raw_packet_recv=item.get('raw_packet_recv', ''),
            raw_packet_send=item.get('raw_packet_send', ''),
            data_type=item.get('data_type', '16-bit Integer'),
            byte_count=item.get('byte_count')
        )
        session.add(modbus_result)

# Commit the transaction
session.commit()