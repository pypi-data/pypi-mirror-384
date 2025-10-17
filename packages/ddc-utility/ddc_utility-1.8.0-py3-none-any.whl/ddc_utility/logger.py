import logging
import os
import sys
import time

# Set the timezone to UTC
logging.Formatter.converter = time.gmtime

# Create a custom logger for your modules
log = logging.getLogger(__name__)

# Create a handler for your logger
handler = logging.StreamHandler(stream=sys.stdout)

# Create a formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

handler.setFormatter(formatter)

# Add the handler to your logger
log.addHandler(handler)
loglevel = os.getenv("LOG_LEVEL", "INFO")
log.setLevel(loglevel)