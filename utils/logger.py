import logging


class CustomLogger(logging.Logger):
    def __init__(self, name: str, log_file: str = "app.log"):
        # Initialize base logger:
        super().__init__(name, logging.DEBUG)

        # Create a formatter:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console: INFO level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

        # File: DEBUG level
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)


if __name__ == "__main__":
    logger = CustomLogger("logger")
    logger.debug("Debug log")
    logger.info("Info log")
