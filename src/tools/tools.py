import os
import sys
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_SERVER_SCRIPT = "mcp_server/server.py"

_mcp_config = {
    "flight-booking": {
        "command": sys.executable,
        "args": [MCP_SERVER_SCRIPT],
        "transport": "stdio",
        "env": {
            **os.environ,
            "FLIGHT_API_USERNAME": os.getenv("FLIGHT_API_USERNAME", "admin"),
            "FLIGHT_API_PASSWORD": os.getenv("FLIGHT_API_PASSWORD", "changeme"),
        },
    }
}


async def _load_tools():
    client = MultiServerMCPClient(_mcp_config)
    return await client.get_tools()


tools = asyncio.run(_load_tools())
