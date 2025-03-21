from datetime import datetime

import tzlocal

from utils.common import FRONTEND_PATH


ITEMS = {
    "Collection": {
        "icon": f"{FRONTEND_PATH}/icons/folder.png",
        "icon_simple": f"{FRONTEND_PATH}/icons/folder.png",
        "item_handler": "Collection"
    },
    "Modbus": {
        "icon": f"{FRONTEND_PATH}/icons/modbus.png",
        "icon_simple": f"{FRONTEND_PATH}/icons/modbus_simple.png",
        "item_handler": "ModbusRequest"
    },
    "ModbusRequest": {
        "icon": f"{FRONTEND_PATH}/icons/modbus.png",
        "icon_simple": f"{FRONTEND_PATH}/icons/modbus_simple.png",
        "item_handler": "ModbusRequest"
    }
}


def get_model_value(item: object, key: str, replace_if_none: str | int = "-"):
    if hasattr(item, key):
        value = getattr(item, key)
    else:
        value = "Unknown"

    if value is None:
        return replace_if_none
    elif type(value) == list:
        return value
    else:
        return str(value)


def convert_timestamp(timestamp_str: str):
    # Parse the input timestamp
    dt = datetime.fromisoformat(timestamp_str.rstrip("Z"))  # Remove 'Z' if present

    # Convert to local timezone using tzlocal
    local_tz = tzlocal.get_localzone()
    dt = dt.astimezone(local_tz)

    # Format to show at least seconds
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def convert_time(seconds: str | float) -> str:
    """Convert time from seconds to the most appropriate unit (s, ms, µs, ns)."""
    if isinstance(seconds, str):
        seconds = float(seconds)

    if seconds >= 1:
        return f"{seconds:.3f} s"
    elif seconds >= 1e-3:
        return f"{seconds * 1e3:.3f} ms"
    elif seconds >= 1e-6:
        return f"{seconds * 1e6:.3f} µs"
    else:
        return f"{seconds * 1e9:.3f} ns"
