# *TODOs KANBAN*

## Priority

TODO: decouple backend from PYQT/SIDE
    - TODO: History tab.
    - TODO: Collection results.

TODO: tab to show description

TODO: execution session as header

TODO: STUDY - continuous requests in a request type, like a background process or a number of consecutive calls

TODO: HOME page with running instances.

TODO: migrate QT to PYSIDE

TODO: MVP 1 documentation

## Future LOW PRIORITY

TODO: separate both repository model and backend DTOs -- SEE FINAL DOCUMENTATION
✔️ Use SQLAlchemy models for persistence
✔️ Use dataclasses / Pydantic / dicts for business logic and API interaction

TODO: control the maximum number of results to save

TODO: clear results button

TODO: running an object and change to another must show it is not being runned. Show running instances in notification bar and link to home page which must have all of them.

TODO: delete client and run_options items when a request is removed

TODO: increase SQLite performance:
- Moving elements is a slow operation.
- UI updates must not reload items.
- Update operations must have background process.
- Test UI on low performance computer - Docker with low resources.

TODO: decimal numbers on polling interval and delay

TODO: add foreign keys and relationships - cascade deletes: https://www.codearmo.com/python-tutorial/sql-alchemy-foreign-keys-and-relationships#google_vignette

TODO: collections must have table view option and show history

TODO: Protect SQLite by encrypting

TODO: raise exception if requests have children. It must be a check in post_init dataclass

TODO: long texts show ellipsis + tooltip to avoid overflow

TODO: BATCH execution 

TODO: Test without automatically reconnecting client

TODO: Data types convert with LSB or MSB - compare with modscan

TODO: documentation

TODO: Pre-request conditions as time sleep

TODO: Splitter must be a component with stretch factor: not expand on first element and expand on second, always.

TODO: QGridLayout custom component must read table items by key str, not list. It must be a dictionary for better identification

TODO: process raw data to extract registers from write multiple registers

TODO: disable edit items on response table

TODO: export button is broken

TODO: execute button maintains like clicked. Avoid to be clicked until request has reached

TODO: results table. Think about how to adjunts results table to show all return text

TODO: add description tab to all requests

TODO: think about moving general results tab to top view. Or add vertical splitter to show all information directly

TODO: improve usability: save last tab opened in each request

TODO: Print all results in different format types

TODO: add connection name for reusability

TODO: allow to reuse "previous" connections

TODO: allow to export results

TODO: MQTT

TODO: add_widget method of custom qgridlayout must save by key, so accessing its elements can be easier and more clear than an index.

TODO: repository layer with relationships, not joins.

## Future pymodbus

TODO: Custom exceptions - Mask pymodbus internals: https://www.simplymodbus.ca/exceptions.htm

TODO: Modbus TLS/Socket/ASCII

TODO: Understand read discrete input modbus response

## Documentation

### separate both repository model and backend DTOs

Step 1: Define your SQLAlchemy model

# models/device.py
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str]
    status: Mapped[str]

🧾 Step 2: Define your DTO

# dtos/device_dto.py
from dataclasses import dataclass

@dataclass
class DeviceDTO:
    id: int
    name: str
    type: str
    status: str

🔁 Step 3: Write reusable converters

You can keep them in a converters/device_converter.py file:

# converters/device_converter.py
from models.device import Device
from dtos.device_dto import DeviceDTO

def to_dto(device: Device) -> DeviceDTO:
    return DeviceDTO(
        id=device.id,
        name=device.name,
        type=device.type,
        status=device.status
    )

def from_dto(dto: DeviceDTO) -> Device:
    return Device(
        id=dto.id,
        name=dto.name,
        type=dto.type,
        status=dto.status
    )

Optional: you can even pass **asdict(dto) if you’re careful with field alignment.