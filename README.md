# Confluence MCP Server

A local, private MCP (Model Context Protocol) server for interacting with a Confluence instance. This server allows an AI agent (like Cascade) to perform actions on your Confluence space via a standardized tool interface.

## Features

Provides the following Confluence actions as MCP tools:
*   `Get_Page`: Retrieves the content of a specific Confluence page.
*   `search_pages`: Searches for pages in Confluence based on a query.
*   `get_spaces`: Lists available Confluence spaces.
*   `update_page`: Updates an existing Confluence page.
*   `create_page`: Creates a new page in a specified Confluence space.
*   `get_comments`: Retrieves comments from a Confluence page.
*   `add_comment`: Adds a comment to a Confluence page.
*   `get_attachments`: Lists attachments for a Confluence page.
*   `add_attachment`: Adds an attachment to a Confluence page.

## Prerequisites

*   Python 3.9+
*   Access to a Confluence instance (Cloud or Server)
*   A Confluence API Key (see [Atlassian Documentation](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) for how to create one)

## Setup Instructions

1.  **Clone the Repository (if applicable) or Create Project Directory:**
    Ensure you have all project files in a local directory. The project root directory is `c:\Users\chris\Documents\Confluence-MCP-Server_Claude`.

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv .venv
    ```
    Activate the virtual environment:
    *   Windows:
        ```bash
        .\.venv\Scripts\activate
        ```
    *   macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```

3.  **Install Dependencies:**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the `.env_example` file to a new file named `.env`:
        ```bash
        # For Windows command prompt
        copy .env_example .env
        # For PowerShell
        # Copy-Item .env_example .env
        # For macOS/Linux
        # cp .env_example .env
        ```
    *   Open the `.env` file and update the following variables with your Confluence instance details:
        *   `CONFLUENCE_URL`: Your full Confluence base URL (e.g., `https://your-domain.atlassian.net/wiki`)
        *   `CONFLUENCE_USERNAME`: The email address associated with your Confluence account and API key.
        *   `CONFLUENCE_API_KEY`: Your generated Confluence API Key.
        *   `PORT` (Optional): The port on which the MCP server will run. Defaults to 8000.

## Running the Server

Once configured, you can run the MCP server using Uvicorn. **Navigate to the project root directory (`c:\Users\chris\Documents\Confluence-MCP-Server_Claude`) in your terminal before running the command.**

```bash
uvicorn confluence_mcp_server.main:app --reload --port <your_configured_port_or_8000>
```
For example, if your `.env` file has `PORT=8080`, and you are in the project root directory, you would run:
```bash
uvicorn confluence_mcp_server.main:app --reload --port 8080
```
If no port is specified in `.env` (and it defaults to 8000), run from the project root:
```bash
uvicorn confluence_mcp_server.main:app --reload
```

The `--reload` flag enables auto-reloading when code changes are detected, which is useful during development.

## Connecting with Claude Desktop (or other MCP Clients)

Once the Confluence MCP Server is running, you can connect it to MCP-compatible clients like Claude Desktop.

1.  **Ensure the Server is Running:**
    Follow the "Running the Server" instructions above. By default, the server will be accessible at `http://127.0.0.1:8000` (or `http://localhost:8000`). If you configured a different port in your `.env` file, use that port instead (e.g., `http://127.0.0.1:YOUR_PORT`).

2.  **Configure Your MCP Client (e.g., Claude Desktop):**
    *   In your MCP client's settings or configuration area where you can add new MCP servers, you will typically need to provide the **Base URL** of this Confluence MCP server.
    *   Enter the URL from step 1 (e.g., `http://127.0.0.1:8000`).
    *   **Important:** The server's `/tools` endpoint (e.g., `http://127.0.0.1:8000/tools/`) is what clients use to discover the available Confluence actions. The `/tools/execute` endpoint (e.g., `http://127.0.0.1:8000/tools/execute`) is used to run them. Your client should be configured to use the base URL, and it will append `/tools` or `/tools/execute` as needed based on the MCP specification.

3.  **CORS Configuration:**
    This Confluence MCP server has been configured with Cross-Origin Resource Sharing (CORS) to allow requests from any origin (`*`). This permissive setting is suitable for local development and connecting with clients like Claude Desktop. For production environments, you might want to restrict the allowed origins.

4.  **Verify Connection:**
    After adding the server to your MCP client, the client should be able to:
    *   Discover the available Confluence tools (e.g., `get_page`, `search_pages`, etc.) by querying the `/tools` endpoint.
    *   Execute these tools by sending requests to the `/tools/execute` endpoint.

Refer to your specific MCP client's documentation for detailed instructions on adding and managing MCP tool servers.

## Usage

(This section will be updated as the MCP server and its tools are implemented. It will describe how an agent can interact with the `/tools` and `/execute` endpoints.)

## Project Structure

```
confluence_mcp_server/
|-- .env_example            # Example for environment variables
|-- .venv/                  # Python virtual environment (if created here)
|-- mcp_actions/            # Directory for Confluence action implementations
|   |-- __init__.py
|   |-- page_actions.py     # Logic for page-related tools
|   |-- comment_actions.py  # Logic for comment-related tools
|   |-- attachment_actions.py # Logic for attachment-related tools
|   |-- space_actions.py    # Logic for space-related tools
|   |-- schemas.py          # Pydantic models for tool inputs/outputs
|-- main.py                 # Main FastAPI application and MCP endpoints
|-- requirements.txt        # Python dependencies
|-- task.md                 # Development task tracking
|-- README.md               # This file
```

## Contributing
(Details to be added if this were a collaborative project)

```
{{ ... }}
          "CONFLUENCE_API_KEY": "YOUR_CONFLUENCE_API_KEY_HERE",
          "CONFLUENCE_USERNAME": "YOUR_CONFLUENCE_EMAIL_HERE",
          "CONFLUENCE_URL": "YOUR_CONFLUENCE_INSTANCE_URL_HERE",
          "PORT": "8001" // Ensure this matches the port your server is running on
        }
      }
    ]
  }
  ```

  **Explanation of Fields:**
  *   `"name"`: A unique identifier for this MCP server configuration (e.g., `"confluence-mcp-local-dev"`).
  *   `"command"`: The full path to the Python executable within your project's virtual environment (e.g., `"C:\path\to\your\project\Confluence-MCP-Server_Claude\.venv\Scripts\python.exe"` on Windows or `"/path/to/your/project/Confluence-MCP-Server_Claude/.venv/bin/python"` on Linux/macOS).
  *   `"args"`: Arguments to pass to the Python interpreter. This should run Uvicorn targeting your FastAPI application.
      *   `"-m"`, `"uvicorn"`: Tells Python to run the `uvicorn` module.
      *   `"confluence_mcp_server.main:app"`: The path to your FastAPI application instance.
      *   `"--host"`, `"127.0.0.1"`: Specifies the host to bind to.
      *   `"--port"`, `"8001"`: Specifies the port to listen on. **Ensure this matches the `PORT` environment variable set below and is not already in use.**
      *   `"--reload"`: (Optional) Enables auto-reload for development. Remove for production.
  *   `"cwd"`: The current working directory for the server process. This should be the root of your `Confluence-MCP-Server_Claude` project directory.
  *   `"env"`: Environment variables to be set for the server process:
      *   `"PYTHONPATH"`: **Crucial for ensuring Python can find your `confluence_mcp_server` module.** Set this to the root of your project (e.g., `"C:\path\to\your\project\Confluence-MCP-Server_Claude"`).
      *   `"CONFLUENCE_URL"`, `"CONFLUENCE_USERNAME"`, `"CONFLUENCE_API_KEY"`: Your Confluence credentials.
      *   `"PORT"`: The port number the Uvicorn server inside your MCP server will try to use. **This must match the `--port` argument above.**

3.  **Restart Claude Desktop:** After saving the `mcp_servers.json` file, fully restart Claude Desktop for the changes to take effect.

4.  **Connect to the Server:** In Claude Desktop, attempt to connect to the `confluence-mcp-local-dev` (or whatever name you chose) server. You should see logs from your server in the Claude Desktop MCP panel indicating a connection and tool discovery.

### Via Docker (Production/Simplified Deployment)

(Instructions to be added once Dockerfile and docker-compose.yml are finalized in Phase 6)

## Project Structure
{{ ... }}
