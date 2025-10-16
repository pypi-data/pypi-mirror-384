import loguru
from mascope_jupyter_widgets.mascope_data.access import (
    get_mjw_mode,
)

# Configure logging
MJW_DEV_MODE = get_mjw_mode()  # Get the MJW_DEV_MODE environment variable
loguru.logger.remove()
loguru.logger.add(
    print,
    level="DEBUG" if MJW_DEV_MODE else "INFO",
    format="{time} - {level} - {message}",
)  # Log to the console
logger = loguru.logger  # Create a shared logger
