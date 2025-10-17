from mcp.server.fastmcp import FastMCP


# region MCP Math
mcp = FastMCP("Math")

@mcp.tool(description="A simple add tool")
def add(a: int, b: int) -> int:
    """Adds two integers.
       Args:
         a: The first integer.
         b: The second integer.
    """
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two integers.
       Args:
         a: The first integer.
         b: The second integer.
    """
    return a * b
# endregion


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # mcp.run(transport="sse")
    # search_mcp.run(transport="sse", mount_path="/search")


