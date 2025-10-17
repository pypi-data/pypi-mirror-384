from datetime import datetime
from mcp.server.fastmcp import FastMCP

# region MCP Weather
mcp = FastMCP("Weather")

@mcp.tool()
def get_weather(location: str) -> str:
    return "Cloudy"

@mcp.tool()
def get_time() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# endregion


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # mcp.run(transport="sse")
    # search_mcp.run(transport="sse", mount_path="/search")


