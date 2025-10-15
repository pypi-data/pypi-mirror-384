
from mcp.server.fastmcp import Context, FastMCP


# region MCP Math
mcp = FastMCP("resource")


@mcp.resource("config://settings")
def get_settings() -> str:
    """Get application settings."""
    return """{
  "theme": "dark",
  "language": "en",
  "debug": false
}"""

@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read a document by name."""
    # This would normally read from disk
    path = "/Users/zhaoxuefeng/GitHub/prompt_writing_assistant/tests/temp_file/"
    path += name
    with open(path,'r') as f:
        return f.read()

@mcp.resource("file://notes/{name}")
def read_notes(name:str)-> str:
    """ 阅读备忘录"""

    return "你要做王子"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

