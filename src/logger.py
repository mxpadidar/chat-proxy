import logging


class Logger:
    """
    Singleton class to log messages to the console
    """

    logger: logging.Logger
    instance: "Logger"
    initialized = False

    def __new__(cls, *args, **kwargs) -> "Logger":
        if not hasattr(cls, "instance"):
            cls.instance = super(Logger, cls).__new__(cls)
        return cls.instance

    def __init__(self, name: str) -> None:
        if self.initialized:
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(console_handler)

        self.initialized = True

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)
