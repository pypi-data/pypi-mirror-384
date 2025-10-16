import logging

logger = logging.getLogger(__name__)

# Add color to error logs
class ColoredFormatter(logging.Formatter):
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.RED}{record.msg}{self.RESET}"
        elif record.levelno >= logging.WARNING:
            record.msg = f"{self.YELLOW}{record.msg}{self.RESET}"
        return super().format(record)

# Apply colored formatter to the logger
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    '[SWAI CLI] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logger.setLevel(logging.INFO)
handler.setLevel(logging.INFO)

logger.handlers = [handler]
