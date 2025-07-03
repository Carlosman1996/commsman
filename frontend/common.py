import traceback
from datetime import datetime

import tzlocal
from PyQt6.QtGui import QIcon
import weakref

from config import FRONTEND_PATH
from utils.logger import CustomLogger


ITEMS = {
    "App": {
        "icon": f"{FRONTEND_PATH}/fixtures/icons/commsman.ico",
        "icon_simple": f"{FRONTEND_PATH}/fixtures/icons/commsman.png",
        "item_handler": "App"
    },
    "Collection": {
        "icon": f"{FRONTEND_PATH}/fixtures/icons/folder.png",
        "icon_simple": f"{FRONTEND_PATH}/fixtures/icons/folder.png",
        "item_handler": "Collection"
    },
    "Modbus": {
        "icon": f"{FRONTEND_PATH}/fixtures/icons/modbus.png",
        "icon_simple": f"{FRONTEND_PATH}/fixtures/icons/modbus_simple.png",
        "item_handler": "ModbusRequest"
    },
    "ModbusRequest": {
        "icon": f"{FRONTEND_PATH}/fixtures/icons/modbus.png",
        "icon_simple": f"{FRONTEND_PATH}/fixtures/icons/modbus_simple.png",
        "item_handler": "ModbusRequest"
    }
}


def get_model_value(item: dict, key: str, replace_if_none: str | int = "-"):
    value = item.get(key, "Unknown")

    if value is None:
        return replace_if_none
    elif type(value) == list:
        return value
    else:
        return str(value)


def get_icon(text):
    if text == "Pending":
        return QIcon.fromTheme("go-next")  # Green check icon
    elif text == "OK":
        return QIcon.fromTheme("dialog-ok")  # Green check icon
    elif text == "Failed":
        return QIcon.fromTheme("dialog-error")  # Red X icon
    elif text == "Running":
        return QIcon.fromTheme("go-next")  # Green check icon
    else:
        raise NotImplementedError


def convert_timestamp(timestamp: str | datetime):
    if isinstance(timestamp, str):
        # Parse the input timestamp
        dt = datetime.fromisoformat(timestamp.rstrip("Z"))  # Remove 'Z' if present
    else:
        dt = timestamp

    # Convert to local timezone using tzlocal
    local_tz = tzlocal.get_localzone()
    dt = dt.astimezone(local_tz)

    # Format to show at least seconds
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


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


class SafeCallback:
    def __init__(self, method):

        self.logger = CustomLogger(name=__name__)
        self._method_ref = weakref.WeakMethod(method)

    def __call__(self, *args, **kwargs):
        method = self._method_ref()

        if method is not None:
            try:
                self.logger.debug(f"Calling method {method.__name__}")
                method(*args, **kwargs)
            except Exception as e:
                self.logger.info("Exception in SafeCallback:", e)
                traceback.print_exc()
        else:
            self.logger.info("Window is gone, callback skipped.")
