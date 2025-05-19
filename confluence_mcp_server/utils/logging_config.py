# confluence_mcp_server/utils/logging_config.py
import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Sets up basic logging for the application.
    """
    # Define a format that includes timestamp, level, logger name, and message
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
    
    # Basic configuration that logs to stdout
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
        ]
    )
    
    # You can also customize specific loggers here if needed
    # For example, to reduce verbosity of certain libraries:
    # logging.getLogger("httpx").setLevel(logging.WARNING)
    # logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {logging.getLevelName(level)}")

if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    logging.getLogger("root_test").debug("This is a debug message from root_test.")
    logging.getLogger("root_test").info("This is an info message from root_test.")
    logging.getLogger("another.module").warning("This is a warning from another.module.")

