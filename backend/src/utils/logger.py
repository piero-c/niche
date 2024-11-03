import logging
import colorlog

# Define the SUCCESS level as 25 (between INFO and WARNING)
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

# Create a method to log at the SUCCESS level
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)

# Add the success method to the Logger class
logging.Logger.success = success

# Create a handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create a formatter with colors, including the custom SUCCESS level
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'SUCCESS':  'bold_green',  # Custom color for SUCCESS
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
