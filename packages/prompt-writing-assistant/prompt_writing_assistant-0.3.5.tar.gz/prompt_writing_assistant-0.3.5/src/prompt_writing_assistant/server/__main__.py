# server
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prompt_writing_assistant.log import Log
from dotenv import load_dotenv, find_dotenv
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
import argparse
import uvicorn

from .mcp.math import mcp as fm_math
from .mcp.weather import mcp as fm_weather


default = 8007

dotenv_path = find_dotenv()
load_dotenv(dotenv_path, override=True)
logger = Log.logger


# Combine both lifespans
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # Run both lifespans
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(fm_math.session_manager.run())
        await stack.enter_async_context(fm_weather.session_manager.run())
        yield

app = FastAPI(
    title="LLM Service",
    description="Provides an OpenAI-compatible API for custom large language models.",
    version="1.0.1",
    # debug=True, 
    # docs_url="/api-docs",
    lifespan=combined_lifespan
)

# --- Configure CORS ---
origins = [
    "*", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specifies the allowed origins
    allow_credentials=True,  # Allows cookies/authorization headers
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers (Content-Type, Authorization, etc.)
)
# --- End CORS Configuration ---




app.mount("/math", fm_math.streamable_http_app()) # /math/mcp
app.mount("/weather", fm_weather.streamable_http_app()) # /weather/mcp





@app.get("/")
async def root():
    """server run"""
    return {"message": "LLM Service is running."}


@app.get("/api/status")
def status():
    return {"status": "ok"}

@app.get("/api/list-routes/")
async def list_fastapi_routes(request: Request):
    routes_data = []
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            routes_data.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods),
                "endpoint": route.endpoint.__name__ # Get the name of the function
            })
    return {"routes": routes_data}



if __name__ == "__main__":
    # 这是一个标准的 Python 入口点惯用法
    # 当脚本直接运行时 (__name__ == "__main__")，这里的代码会被执行
    # 当通过 python -m YourPackageName 执行 __main__.py 时，__name__ 也是 "__main__"
    # 27
    
    parser = argparse.ArgumentParser(
        description="Start a simple HTTP server similar to http.server."
    )
    parser.add_argument(
        "port",
        metavar="PORT",
        type=int,
        nargs="?",  # 端口是可选的
        default=default,
        help=f"Specify alternate port [default: {default}]",
    )
    # 创建一个互斥组用于环境选择
    group = parser.add_mutually_exclusive_group()

    # 添加 --dev 选项
    group.add_argument(
        "--dev",
        action="store_true",  # 当存在 --dev 时，该值为 True
        help="Run in development mode (default).",
    )

    # 添加 --prod 选项
    group.add_argument(
        "--prod",
        action="store_true",  # 当存在 --prod 时，该值为 True
        help="Run in production mode.",
    )
    args = parser.parse_args()

    if args.prod:
        env = "prod"
    else:
        # 如果 --prod 不存在，默认就是 dev
        env = "dev"

    port = args.port

    if env == "dev":
        port += 100
        Log.reset_level("debug", env=env)
        reload = True
        app_import_string = (
            f"{__package__}.__main__:app"  # <--- 关键修改：传递导入字符串
        )
    elif env == "prod":
        Log.reset_level(
            "info", env=env
        )  # ['debug', 'info', 'warning', 'error', 'critical']
        reload = False
        app_import_string = app
    else:
        reload = False
        app_import_string = app

    # 使用 uvicorn.run() 来启动服务器
    # 参数对应于命令行选项
    uvicorn.run(
        app_import_string, host="0.0.0.0", port=port, reload=reload  # 启用热重载
    )
