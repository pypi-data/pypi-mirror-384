import logging

logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set the log format
    handlers=[
        logging.FileHandler('py4heappe.log')  # Log to a file
    ]
)

logger = logging.getLogger(__name__)