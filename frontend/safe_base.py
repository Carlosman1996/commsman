import types
import traceback
import functools
from PyQt6.QtWidgets import QWidget

def catch_exceptions(method):
    """Decorator that catches and logs exceptions in methods."""
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:
            cls_name = args[0].__class__.__name__ if args else "<unknown>"
            print(f"[Exception] in {cls_name}.{method.__name__}: {e}")
            print(f"  args: {args}")
            print(f"  kwargs: {kwargs}")
            print(traceback.format_exc())
            # Optional: show QMessageBox or log to file here
    return wrapper


class SafeWidget(QWidget):
    """
    Base QWidget class that automatically wraps subclass methods with exception catching.

    To use: subclass this instead of QWidget directly.
    """
    def __init_subclass__(cls, *args, **kwargs):
        """
        Objective: Defensive programming.

        ⚙️ __init_subclass__ – Centralized Exception Handling

        We use the __init_subclass__ method in our base UI class to automatically wrap all methods in child classes
        with a generic exception handler (catch_exceptions). This helps ensure that unhandled exceptions in the UI
        logic are caught and logged properly without requiring a try/except block in every method.

        🧠 How It Works
        When you define a new subclass of Base, Python automatically calls Base.__init_subclass__. This method:

        1. Iterates over all methods defined in the subclass.
        2. For each method that is a plain function (types.FunctionType):
            - Wraps it with the catch_exceptions decorator.
        3. Skips:
            - Magic methods like __init__, __str__, etc.
            - Inherited methods (e.g., from Base or other mixins).
            - Static methods and class methods.
        """
        super().__init_subclass__(*args, **kwargs)

        for attr_name, attr_value in cls.__dict__.items():
            if isinstance(attr_value, types.FunctionType) and not attr_name.startswith("__"):
                # Only wrap true functions, not descriptors or inherited methods
                setattr(cls, attr_name, catch_exceptions(attr_value))
