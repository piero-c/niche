import logging
import colorlog

# Create a handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create a formatter with colors
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Set formatter to handler
handler.setFormatter(formatter)

# Get the root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
