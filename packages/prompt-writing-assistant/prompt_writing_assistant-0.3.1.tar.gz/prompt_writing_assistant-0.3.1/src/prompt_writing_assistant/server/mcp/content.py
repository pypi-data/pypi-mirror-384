
from mcp.server.fastmcp import Context, FastMCP, Icon
from prompt_writing_assistant.file_manager import ContentManager, TextType
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import BaseModel, Field
from prompt_writing_assistant.prompt_helper import IntellectType,Intel


content_manager = ContentManager()
intels = Intel()

mcp = FastMCP("Content")

@mcp.prompt(title="Code Review")
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"


@mcp.prompt(title="Debug Assistant")
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]


@mcp.tool()
def save_content(text:str)->str:
    """
    text : 需要存储的内容
    return : 返回是否存储成功的信息
    """
    result =content_manager.save_content_auto(
                text = text)
    return result

@mcp.tool()
def similarit_content(text: str,limit: int):
    """
    text : 待查询的文字, 进行匹配
    limit : 查询的数量
    """
    
    result = content_manager.similarity(
        content = text,
        limit = limit
    )
    return result

@mcp.tool()
def get_prompts(prompt_id: str,version: str = "1.0"):
    """
    prompt_id : 待查询的文字, 进行匹配
    limit : 查询的数量
    """
    result = intels.get_prompts_from_sql(
        table_name = "prompts_data",
        prompt_id = prompt_id,
        version=version,
        )
    return result

@mcp.tool()
def list_cities() -> list[str]:
    """Get a list of cities"""
    return ["London", "Paris", "Tokyo"]






class WeatherData(BaseModel):
    """Weather information structure."""

    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str
    wind_speed: float


@mcp.tool() # icons=[icon]
def get_weather(city: str) -> WeatherData:
    """Get weather for a city - returns structured data."""
    # Simulated weather data
    return WeatherData(
        temperature=22.5,
        humidity=45.0,
        condition="sunny",
        wind_speed=5.2,
    )


from PIL import Image as PILImage
from mcp.server.fastmcp import FastMCP, Image

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")



if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # mcp.run(transport="sse")
    # search_mcp.run(transport="sse", mount_path="/search")


