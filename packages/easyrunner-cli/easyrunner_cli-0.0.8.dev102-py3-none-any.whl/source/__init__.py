import logging

# Configure root logger (this will affect all loggers including the library's)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(name)s]:  %(message)s'
)

# set log level for third party libraries
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("invoke").setLevel(logging.WARNING)
logging.getLogger("fabric").setLevel(logging.WARNING)

# Get root logger and allow debug override via CLI flag
logger = logging.getLogger()
