# 导入FastMCP库
from fastmcp import FastMCP, Context
from fastmcp.resources import FileResource
from pathlib import Path
import httpx
# 导入 requests 库用于外部 HTTP 请求
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()  # 自动加载 .env 文件中的环境变量
# 初始化FastMCP实例，参数为服务名称
mcp = FastMCP("mcp-server-demo")


# 获取指定城市天气的工具函数
@mcp.tool()
async def get_weather(city: str) -> dict:
    """
    获取城市天气预报
    参数:
        city (str): 城市名称
    返回:
        dict: 包含天气预报信息的字典
    示例:
        >>> get_weather("Guangzhou")
    """
    url = "https://api.seniverse.com/v3/weather/now.json"
    params = {
        "key": os.getenv("SENIVERSE_API_KEY"),
        # "key": SENIVERSE_API_KEY,
        "location": city,
        "language": "zh-Hans",
        "unit": "c"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()

# 使用装饰器注册工具函数
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    阶梯加法计算工具
    参数:
        a (int): 第一个加数
        b (int): 第二个加数
    返回:
        int: 返回a + b * 2的结果
    示例:
        >>> add(2, 3)
        8
        >>> add(5, 1)
        7
    """
    return a + b * 2
# 注册减法工具
@mcp.tool()
def subtract(a: float, b: float) -> float:
    """返回 a - b 的结果"""
    return a - b
# 解释：定义减法函数并注册为 MCP 工具

# 注册乘法工具
@mcp.tool()
def multiply(a: float, b: float) -> float:
    """返回 a * b 的结果"""
    return a * b
# 解释：定义乘法函数并注册为 MCP 工具

# 注册除法工具
@mcp.tool()
def divide(a: float, b: float) -> float:
    """返回 a / b 的结果，b 不能为 0"""
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b
# 解释：定义除法函数并注册为 MCP 工具，b 为 0 时抛出异常

@mcp.tool()
def get_holiday(holiday: str) -> dict:
    """获取节假日信息"""
    return {"holiday": holiday, "temp": 20}

@mcp.tool()
def get_current_time() -> dict:
    """获取当前时间信息"""
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(now.timestamp())
    }


def find_user_by_email(email: str) -> dict:
    """Pseudocode to find a user by email."""
    # In a real implementation, this would query a database or external service
    return {"email": email, "name": "John Doe", "id": 123}
def find_user_by_name(name: str) -> dict:
    """Pseudocode to find a user by name."""
    # In a real implementation, this would query a database or external service
    return {"name": name, "email": "Bili@example.com", "id": 456}
# Manually apply multiple decorators to the same function
# Template with multiple parameters and annotations
@mcp.resource(
    "repos://{owner}/{repo}/info",)
def get_repo_info(owner: str, repo: str) -> dict:
    """Retrieves information about a GitHub repository."""
    # In a real implementation, this would call the GitHub API
    return {
        "owner": owner,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "stars": 120,
        "forks": 48
    }

# Resource returning JSON data (dict is auto-serialized)
@mcp.resource("data://config")
def get_config() -> dict:
    """Provides application configuration as JSON."""
    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"],
    }
@mcp.prompt()
def summarize_request(text: str) -> str:
    """Generate a prompt asking for a summary."""
    return f"Please summarize the following text:\n\n{text}"

# 主程序入口
if __name__ == "__main__":
    print("🚀 启动 FastMCP 服务...")
    # 启动FastMCP服务
    mcp.run(
        transport="stdio",  # 使用stdio传输协议
    )