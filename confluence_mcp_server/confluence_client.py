# confluence_mcp_server/confluence_client.py
import os
from dotenv import load_dotenv
from atlassian import Confluence
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

_confluence_client_instance = None

def get_confluence_client() -> Confluence:
    """
    Initializes and returns a Confluence client instance.
    Reads credentials (CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
    from environment variables.
    Caches the client instance for reuse.
    """
    global _confluence_client_instance

    if not all([CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN]):
        logger.error(
            "Missing one or more Confluence connection environment variables: "
            "CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN"
        )
        raise ValueError(
            "Missing Confluence credentials. Please set CONFLUENCE_URL, "
            "CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN in your .env file."
        )

    if _confluence_client_instance is None:
        try:
            logger.info(f"Initializing Confluence client for URL: {CONFLUENCE_URL}")
            _confluence_client_instance = Confluence(
                url=CONFLUENCE_URL,
                username=CONFLUENCE_USERNAME,
                password=CONFLUENCE_API_TOKEN,
                cloud=True  # Assuming Confluence Cloud. Adjust if server.
            )
            # Optional: A quick check to see if client can connect, e.g., get server info
            # try:
            #     server_info = _confluence_client_instance.server_info()
            #     logger.info(f"Successfully connected to Confluence: {server_info.get('baseUrl')}")
            # except Exception as e:
            #     logger.error(f"Failed to connect to Confluence or verify server info: {e}", exc_info=True)
            #     # Depending on strictness, could raise an error here
            #     # raise ConnectionError(f"Failed to connect to Confluence: {e}")

        except Exception as e:
            logger.error(f"Error initializing Confluence client: {e}", exc_info=True)
            # Potentially re-raise or handle appropriately if initialization itself fails
            raise ConnectionError(f"Could not initialize Confluence client: {e}")
    
    return _confluence_client_instance

if __name__ == "__main__":
    # Basic test to verify client initialization
    logging.basicConfig(level=logging.INFO)
    logger.info("Attempting to initialize Confluence client...")
    try:
        client = get_confluence_client()
        logger.info(f"Confluence client initialized: {client}")
        # Example: Try a simple API call if you want to test further
        # For example, to get current user (requires appropriate permissions)
        # current_user = client.get_current_user_details()
        # logger.info(f"Current user: {current_user.get('displayName')}")
    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
    except ConnectionError as ce:
        logger.error(f"Connection error: {ce}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

