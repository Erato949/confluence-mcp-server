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
    Ensure you have all project files in a local directory. Our current working directory is `c:\Users\chris\Documents\Confluence-MCP-Server_Claude\confluence_mcp_server`.

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

Once configured, you can run the MCP server using Uvicorn:

```bash
uvicorn main:app --reload --port <your_configured_port_or_8000>
```
For example, if your `.env` file has `PORT=8080`, you would run:
```bash
uvicorn main:app --reload --port 8080
```
If no port is specified in `.env`, it defaults to 8000:
```bash
uvicorn main:app --reload
```

The `--reload` flag enables auto-reloading when code changes are detected, which is useful during development.

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
