import json
import pathlib
from collections import defaultdict, deque

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import *

DIR_PATH = pathlib.Path(__file__).parent.resolve()


# Load JSON data
with open(f'{DIR_PATH}/project_structure_data.json', 'r') as f:
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
        if result:
            return ', '.join(result)  # Join with commas
        else:
            return None
    else:
        return None


def insert_into_database(item):
    item_dataclass = None

    # Migrate Clients
    if item.get('item_handler') in ["ModbusTcpClient"]:
        client = Client(
            name=item['name'],
            client_type_handler=item['item_handler']
        )
        session.add(client)
        session.commit()

        item_dataclass = ModbusTcpClient(
            name=item['name'],
            item_type=item['item_type'],
            client_id=client.item_id,
            client_type=item['client_type'],
            host=item['host'],
            port=item['port'],
            timeout=item['timeout'],
            retries=item['retries']
        )
        session.add(item_dataclass)
        session.commit()
    if item.get('item_handler') in ["ModbusRtuClient"]:
        client = Client(
            name=item['name'],
            client_type_handler=item['item_handler']
        )
        session.add(client)
        session.commit()

        item_dataclass = ModbusRtuClient(
            name=item['name'],
            item_type=item['item_type'],
            client_id=client.item_id,
            client_type=item['client_type'],
            com_port = item["com_port"],
            baudrate = item["baudrate"],
            parity = item["parity"],
            stopbits = item["stopbits"],
            bytesize = item["bytesize"],
            timeout=item['timeout'],
            retries=item['retries']
        )
        session.add(item_dataclass)
        session.commit()

    # Migrate Run Options
    if item.get('item_handler') in ["RunOptions"]:
        item_dataclass = RunOptions(
            name=item['name'],
            item_type=item['item_type'],
            polling=item['polling'],
            polling_interval=item['polling_interval'],
            delayed_start=item['delayed_start']
        )
        session.add(item_dataclass)
        session.commit()

    # Migrate Collections
    if item.get('item_handler') in ["Collection"]:
        request = Request(
            name=item['name'],
            request_type_handler=item['item_handler']
        )
        session.add(request)
        session.commit()

        item_dataclass = Collection(
            item_id=request.item_id,
            name=item['name'],
            item_type=item['item_type'],
            parent_id=dataclasses_inserted[item.get('parent')].item_id if item.get('parent') else None,
            client_id=dataclasses_inserted[item.get('client')].item_id if item.get('client') else None,
            client_type=item['client_type'],
            position=item.get('position'),
            run_options_id=dataclasses_inserted[item.get('run_options')].item_id,
        )
        session.add(item_dataclass)
        session.commit()

    # Migrate Modbus Requests
    if item.get('item_handler') in ["ModbusRequest"]:
        request = Request(
            name=item['name'],
            request_type_handler=item['item_handler']
        )
        session.add(request)
        session.commit()

        item_dataclass = ModbusRequest(
            item_id=request.item_id,
            name=item['name'],
            item_type=item['item_type'],
            parent_id=dataclasses_inserted[item.get('parent')].item_id if item.get('parent') else None,
            client_id=dataclasses_inserted[item.get('client')].item_id if item.get('client') else None,
            client_type=item['client_type'],
            run_options_id=dataclasses_inserted[item.get('run_options')].item_id,
            position=item.get('position'),
            function=item['function'],
            data_type=item['data_type'],
            slave=item['slave'],
            address=item['address'],
            count=item['count'],
            values=item['values'])
        session.add(item_dataclass)
        session.commit()

    return item_dataclass


def topological_sort_with_position(data):
    # Step 1: Initialize structures
    graph = defaultdict(list)
    in_degree = {key: 0 for key in data}  # Ensure all elements are initialized
    elements = data.copy()  # Keep a reference to original data

    # Step 2: Build the graph and in-degree count
    for key, item in data.items():
        parent_key = item.get('parent')

        # If the item has a parent, establish the relationship
        if parent_key and parent_key in data:
            graph[parent_key].append(key)
            in_degree[key] += 1

        # Ensure children are counted for their dependencies
        if 'children' in item:
            for child_uuid in item['children']:
                if child_uuid in data:  # Only consider valid children
                    graph[key].append(child_uuid)
                    in_degree[child_uuid] += 1

    # Step 3: Separate base elements (no parent and no children)
    base_elements = [key for key in data if not data[key].get('parent') and not data[key].get('children')]
    root_elements = [key for key in data if not data[key].get('parent') and key not in base_elements]

    # Step 4: Perform topological sorting
    queue = deque(base_elements + root_elements)  # Base elements go first
    sorted_elements = []

    while queue:
        current = queue.popleft()
        sorted_elements.append(elements[current])

        # Assign positions to children
        parent_data = elements[current]
        if 'children' in parent_data:
            for position, child_uuid in enumerate(parent_data['children']):
                if child_uuid in elements:
                    elements[child_uuid]['position'] = position

        # Reduce in-degree for children and add them to queue if ready
        for child in graph[current]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Check for cycles
    if len(sorted_elements) != len(data):
        raise ValueError("Cycle detected in the data; topological sort not possible.")

    return sorted_elements

# Example usage:
sorted_items = topological_sort_with_position(data)

# Insert into the database in this order
dataclasses_inserted = {}
for item in sorted_items:
    dataclass_item = insert_into_database(item)  # Replace with your actual DB insertion function
    dataclasses_inserted[item["uuid"]] = dataclass_item

session.commit()
