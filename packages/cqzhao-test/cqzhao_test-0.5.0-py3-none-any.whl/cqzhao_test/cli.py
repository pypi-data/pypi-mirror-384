#!/usr/bin/env python
"""
cqzhao-test - An MCP server powered by FastMCP
Supports: uvx cqzhao-test [--mcp-manifest]
"""

import sys
import json
from typing import Any, Dict, List, cast
from fastmcp import FastMCP, Context
from fastmcp.resources import FileResource
from pathlib import Path
import httpx
import requests
import os
import argparse
from datetime import datetime

# 加载环境变量

# 初始化 MCP 应用
mcp = FastMCP("cqzhao-mcp-server")

# 🔧 工具1：获取天气
@mcp.tool()
async def get_weather(city: str) -> dict:
    """
    获取城市天气预报。
    参数:
        city (str): 城市名称，例如 "Guangzhou"
    返回:
        dict: 包含温度、天气状况等信息
    """
    url = "https://api.seniverse.com/v3/weather/now.json"
    params = {
        "key": 'S9pvanHx_h2g_IYtL',
        "location": city,
        "language": "zh-Hans",
        "unit": "c"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return {
                "temperature": data["results"][0]["now"]["temperature"],
                "condition": data["results"][0]["now"]["text"],
                "city": data["results"][0]["location"]["name"]
            }
    except Exception as e:
        return {"error": f"Weather API error: {str(e)}"}


# 🔧 工具2：加法 a + b * 2
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    阶梯加法计算器：a + b * 2
    示例: add(2, 3) → 8
    """
    return a + b * 2


# 🔧 工具3：减法 a - b
@mcp.tool()
def subtract(a: float, b: float) -> float:
    """
    减法计算：a - b
    """
    return a - b


# 🔧 工具4：获取当前时间
@mcp.tool()
def get_current_time() -> dict:
    """
    获取当前时间和时间戳
    """
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(now.timestamp())
    }
from pydantic import BaseModel
from typing import Literal
# ===== 定义每个工具的输入模型 =====
class GetWeatherInput(BaseModel):
    city: str
class AddInput(BaseModel):
    a: int
    b: int
class SubtractInput(BaseModel):
    a: float
    b: float
class GetCurrentTimeInput(BaseModel):
    pass  # 无参数
# ===== TOOLS 注册：包含函数、输入模型和描述 =====
TOOLS = {
    "get_weather": {
        "function": get_weather,
        "input_model": GetWeatherInput,
        "description": "获取城市天气预报。参数: city (str)"
    },
    "add": {
        "function": add,
        "input_model": AddInput,
        "description": "阶梯加法计算器：a + b * 2"
    },
    "subtract": {
        "function": subtract,
        "input_model": SubtractInput,
        "description": "减法计算：a - b"
    },
    "get_current_time": {
        "function": get_current_time,
        "input_model": GetCurrentTimeInput,
        "description": "获取当前时间和时间戳"
    }
}
# ===== Manifest 生成函数 =====
def generate_manifest():
    tools_list = []
    for name, tool_info in TOOLS.items():
        input_model = tool_info["input_model"]
        schema = input_model.model_json_schema()
        description = tool_info.get("description", "")
        # 移除 title 字段（可选，整洁输出）
        if "title" in schema:
            del schema["title"]
        tools_list.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": schema
            }
        })
    return {"tools": tools_list}
# ===============================
# 主程序入口：支持 --mcp-manifest 和正常运行
# ===============================

def main():
    # ==== 特殊参数处理：输出 manifest ====
    if "--mcp-manifest" in sys.argv:
        manifest = generate_manifest()
        print(json.dumps(manifest), end="")
        return

    # ==== 正常启动 MCP Server ====
    print("🚀 启动 FastMCP 服务...", file=sys.stderr)

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n👋 MCP 服务已关闭。", file=sys.stderr)
    except Exception as e:
        print(f"❌ MCP 运行出错: {e}", file=sys.stderr)
        sys.exit(1)


# ======== 程序入口点 ========
if __name__ == "__main__":
    main()
