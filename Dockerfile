# Confluence MCP Server - Optimized for Smithery.ai
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY confluence_mcp_server/ ./confluence_mcp_server/
COPY smithery.yaml ./
COPY README.md ./

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Expose port
EXPOSE 8000

# Ultra-fast health check for Smithery platform
HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run optimized server with guaranteed lazy loading
CMD ["python", "-m", "confluence_mcp_server.server_http_optimized"]

# Alternative commands:
# For stdio transport (local): CMD ["python", "-m", "confluence_mcp_server.main"]
# For development: CMD ["python", "-m", "confluence_mcp_server.server_http", "0.0.0.0", "8000"] 