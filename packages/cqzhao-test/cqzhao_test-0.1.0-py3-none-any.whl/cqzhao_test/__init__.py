from publish.main import mcp

def main() -> None:
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.run(transport='stdio')
    print("MCP服务已启动，等待工具调用...")
