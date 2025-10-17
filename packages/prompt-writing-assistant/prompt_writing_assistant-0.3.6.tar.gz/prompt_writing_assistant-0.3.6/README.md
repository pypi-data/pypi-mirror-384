uv run mcp dev src/prompt_writing_assistant/mcp.py



```python


@mcp.tool()
async def my_tool(x: int, ctx: Context) -> str:
    """Tool that uses context capabilities.
    
    The Context object provides the following capabilities:

ctx.request_id - Unique ID for the current request
ctx.client_id - Client ID if available
ctx.fastmcp - Access to the FastMCP server instance (see FastMCP Properties)
ctx.session - Access to the underlying session for advanced communication (see Session Properties and Methods)
ctx.request_context - Access to request-specific data and lifespan resources (see Request Context Properties)
await ctx.debug(message) - Send debug log message
await ctx.info(message) - Send info log message
await ctx.warning(message) - Send warning log message
await ctx.error(message) - Send error log message
await ctx.log(level, message, logger_name=None) - Send log with custom level
await ctx.report_progress(progress, total=None, message=None) - Report operation progress
await ctx.read_resource(uri) - Read a resource by URI
await ctx.elicit(message, schema) - Request additional information from user with validation
    
    """
    # The context parameter can have any name as long as it's type-annotated
    return ctx.client_id

```


