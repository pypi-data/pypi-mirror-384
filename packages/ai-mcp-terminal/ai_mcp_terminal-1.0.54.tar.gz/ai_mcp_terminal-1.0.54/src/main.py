#!/usr/bin/env python3
"""
AI-MCP Terminal - 主程序
同时运行MCP服务器和Web服务器
"""
import asyncio
import sys
import os
import threading
import webbrowser
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from terminal_manager import TerminalManager
from web_server import WebTerminalServer


# 全局变量
web_server_instance = None
web_server_started = False


async def start_web_server_background(terminal_manager):
    """在后台启动Web服务器"""
    global web_server_instance, web_server_started
    
    if web_server_started:
        return
    
    web_server_instance = WebTerminalServer(terminal_manager)
    
    # 在单独的线程中运行Web服务器
    def run_web_server():
        import uvicorn
        port = web_server_instance.find_available_port()
        web_server_instance.port = port
        
        # 在启动后打开浏览器
        def open_browser():
            time.sleep(2)
            webbrowser.open(f"http://localhost:{port}")
            print(f"\n[Web界面] 已自动打开浏览器: http://localhost:{port}", file=sys.stderr)
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        config = uvicorn.Config(
            web_server_instance.app,
            host="0.0.0.0",
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        print(f"[Web服务器] 启动在端口: {port}", file=sys.stderr)
        
        # 运行服务器
        asyncio.run(server.serve())
    
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    web_server_started = True
    
    # 等待Web服务器启动
    await asyncio.sleep(2)


async def main():
    """主函数 - 启动所有服务"""
    
    # 创建共享的终端管理器
    terminal_manager = TerminalManager()
    
    # 创建Web服务器
    web_server = WebTerminalServer(terminal_manager)
    
    print("=" * 60, file=sys.stderr)
    print("AI-MCP Terminal Server", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(file=sys.stderr)
    print("正在启动服务...", file=sys.stderr)
    print(file=sys.stderr)
    
    # 启动Web服务器（在后台任务中）
    web_task = asyncio.create_task(web_server.start())
    
    # 等待Web服务器启动
    await asyncio.sleep(2)
    
    print(f"✓ Web服务器已启动: http://localhost:{web_server.port}", file=sys.stderr)
    print(f"✓ MCP服务器运行中 (stdio模式)", file=sys.stderr)
    print(file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(file=sys.stderr)
    
    try:
        # 保持程序运行
        await web_task
    except KeyboardInterrupt:
        print("\n正在关闭服务...", file=sys.stderr)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def cli_main():
    """命令行入口点（用于 pip install 后的命令行调用）"""
    # 检查是否通过MCP客户端调用（stdio模式）
    if sys.stdin.isatty():
        # 直接运行，只启动Web服务器
        asyncio.run(main())
    else:
        # 通过MCP客户端调用，运行MCP服务器（同时启动Web）
        from mcp_server import main as mcp_main
        asyncio.run(mcp_main())


if __name__ == "__main__":
    cli_main()

