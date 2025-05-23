# confluence_mcp_server/utils/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO):
    """
    Sets up basic logging for the application.
    Logs to file instead of stdout to avoid interfering with MCP JSON-RPC protocol.
    """
    # Define a format that includes timestamp, level, logger name, and message
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create file handler with rotation
    log_file = os.path.join(log_dir, "confluence_mcp_server.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger to use file handler only (no stdout)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Clear any existing handlers
    root_logger.handlers.clear()
    # Add only the file handler
    root_logger.addHandler(file_handler)
    
    # Reduce verbosity of certain libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup message (to file, not stdout)
    logger = logging.getLogger(__name__)
    logger.info(f"MCP Server logging configured with level: {logging.getLevelName(level)}")
    logger.info(f"Log file: {log_file}")

if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    logging.getLogger("root_test").debug("This is a debug message from root_test.")
    logging.getLogger("root_test").info("This is an info message from root_test.")
    logging.getLogger("another.module").warning("This is a warning from another.module.")

