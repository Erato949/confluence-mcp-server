#!/usr/bin/env python3
"""
Minimal test server to diagnose Smithery deployment issues
This is the simplest possible MCP server that should work
"""

import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minimal MCP Test Server",
    description="Diagnostic server for Smithery deployment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Ultra-simple health check"""
    logger.info("Health check called")
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint called")
    return {"message": "Minimal MCP Test Server", "status": "running"}

@app.get("/mcp")
async def get_tools():
    """Minimal tool listing for Smithery scanning"""
    logger.info("GET /mcp called - returning minimal tools")
    return {
        "tools": [
            {
                "name": "test_tool",
                "description": "A simple test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Test message"}
                    }
                }
            }
        ]
    }

@app.post("/mcp")
async def post_mcp():
    """Minimal JSON-RPC response"""
    logger.info("POST /mcp called")
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": "test_tool", 
                    "description": "A simple test tool",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Test message"}
                        }
                    }
                }
            ]
        }
    }

if __name__ == "__main__":
    logger.info("Starting minimal test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 