# Confluence MCP Server - Multi-platform Dockerfile
# Supports deployment on Smithery.ai, Docker, and other container platforms

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY confluence_mcp_server/ ./confluence_mcp_server/
COPY smithery.yaml ./
COPY README.md ./

# Create non-root user for security
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Expose port for HTTP transport
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - HTTP server for cloud deployment
CMD ["python", "-m", "confluence_mcp_server.server_http"]

# Alternative commands:
# For stdio transport (local): CMD ["python", "-m", "confluence_mcp_server.main"]
# For development: CMD ["python", "-m", "confluence_mcp_server.server_http", "0.0.0.0", "8000"] 