"""
Web服务器 - 提供Web界面和WebSocket支持
"""
import asyncio
import json
import os
import webbrowser
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .terminal_manager import TerminalManager
except ImportError:
    from terminal_manager import TerminalManager


class WebTerminalServer:
    """Web终端服务器"""
    
    def __init__(self, terminal_manager: TerminalManager):
        import sys
        print(f"[WebServer] __init__开始", file=sys.stderr)
        sys.stderr.flush()
        
        self.app = FastAPI(title="AI-MCP Terminal")
        print(f"[WebServer] FastAPI创建完成", file=sys.stderr)
        sys.stderr.flush()
        
        self.terminal_manager = terminal_manager
        self.active_connections: Set[WebSocket] = set()
        self.port = None
        self.loop = None  # 保存主事件循环引用
        self.shutdown_callback = None  # shutdown回调函数
        
        # 挂载静态文件
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            print(f"[WebServer] 挂载静态文件: {static_dir}", file=sys.stderr)
            sys.stderr.flush()
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        print(f"[WebServer] 注册回调...", file=sys.stderr)
        sys.stderr.flush()
        
        # 注册终端事件回调
        self.terminal_manager.register_callback(self._handle_terminal_event)
        self.terminal_manager.register_callback(self._handle_output_chunk, event_type='output_chunk')
        
        print(f"[WebServer] 设置路由...", file=sys.stderr)
        sys.stderr.flush()
        
        self._setup_routes()
        
        print(f"[WebServer] __init__完成", file=sys.stderr)
        sys.stderr.flush()
    
    async def _handle_terminal_event(self, event_type: str, data: dict):
        """处理终端事件并广播"""
        import sys
        message = {
            "type": event_type,
            **data
        }
        print(f"[DEBUG] Web服务器广播事件: {message}", file=sys.stderr)
        await self._broadcast(message)
    
    def _handle_output_chunk(self, data: dict):
        """处理实时输出块（同步回调，线程安全）"""
        import sys
        # 从同步线程安全地调度到异步事件循环
        try:
            # 使用保存的loop引用
            if not self.loop:
                print(f"[ERROR] 事件循环未初始化！", file=sys.stderr)
                return
            
            loop = self.loop
            chunk_preview = data['chunk'][:50] if len(data['chunk']) > 50 else data['chunk']
            print(f"[实时输出] 准备广播: {data['session_id']}, chunk: {chunk_preview}", file=sys.stderr)
            print(f"[实时输出] 使用事件循环: {loop}, 运行中: {loop.is_running()}", file=sys.stderr)
            
            # 使用线程安全的方式调度协程
            future = asyncio.run_coroutine_threadsafe(
                self._broadcast({
                    "type": "output_chunk",
                    "session_id": data['session_id'],
                    "chunk": data['chunk'],
                    "stream": data['stream']
                }),
                loop
            )
            print(f"[实时输出] 已调度广播任务，Future: {future}", file=sys.stderr)
            
            # 等待结果（超时1秒）
            try:
                result = future.result(timeout=1.0)
                print(f"[实时输出] 广播完成", file=sys.stderr)
            except Exception as e:
                print(f"[实时输出] 广播超时或失败: {e}", file=sys.stderr)
                
        except Exception as e:
            print(f"[ERROR] Failed to broadcast output chunk: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            """返回主页面"""
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            index_file = os.path.join(static_dir, "index.html")
            
            if os.path.exists(index_file):
                with open(index_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return "<h1>AI-MCP Terminal</h1><p>Web界面加载中...</p>"
        
        @self.app.get("/api/sessions")
        async def get_sessions():
            """获取所有会话"""
            sessions = self.terminal_manager.get_all_sessions()
            return {"sessions": sessions}
        
        @self.app.get("/api/sessions/{session_id}")
        async def get_session(session_id: str):
            """获取会话详情"""
            status = self.terminal_manager.get_session_status(session_id)
            if status is None:
                return {"error": "会话不存在"}
            return status
        
        @self.app.get("/api/sessions/{session_id}/output")
        async def get_output(session_id: str, lines: int = 100, only_last_command: bool = False):
            """获取会话输出"""
            import sys
            success, output_list, metadata = self.terminal_manager.get_output(
                session_id, 
                lines=lines,
                only_last_command=only_last_command
            )
            
            # 调试日志
            print(f"[API] get_output: session={session_id}, success={success}, output_count={len(output_list)}", file=sys.stderr)
            if output_list:
                print(f"[API] 第一条输出: {output_list[0]}", file=sys.stderr)
            sys.stderr.flush()
            
            return {
                "success": success,
                "output": output_list,
                "metadata": metadata
            }
        
        @self.app.post("/api/sessions")
        async def create_session(data: dict = None):
            """创建新会话"""
            name = data.get("name") if data else None
            session_id = self.terminal_manager.create_session(name=name)
            
            # 通知所有WebSocket客户端
            await self._broadcast({
                "type": "session_created",
                "session_id": session_id
            })
            
            return {"session_id": session_id}
        
        @self.app.post("/api/sessions/{session_id}/execute")
        async def execute_command(session_id: str, data: dict):
            """执行命令"""
            command = data.get("command", "")
            source = data.get("source", "ai")  # 获取来源，默认为AI
            
            # 异步执行
            asyncio.create_task(
                self._execute_and_broadcast(session_id, command, source)
            )
            
            return {"status": "executing", "session_id": session_id, "command": command}
        
        @self.app.delete("/api/sessions/{session_id}")
        async def kill_session(session_id: str):
            """终止会话"""
            success = await self.terminal_manager.kill_session(session_id)
            
            # 通知所有客户端
            await self._broadcast({
                "type": "session_killed",
                "session_id": session_id
            })
            
            return {"success": success}
        
        @self.app.get("/api/stats")
        async def get_stats():
            """获取统计信息"""
            stats = self.terminal_manager.get_stats()
            memory_check = self.terminal_manager.check_memory_and_suggest_cleanup()
            return {
                "stats": stats,
                "memory_check": memory_check
            }
        
        @self.app.post("/api/shutdown")
        async def shutdown():
            """关闭所有终端和连接，释放资源（但保持MCP服务运行）"""
            import sys
            
            print("[INFO] 开始关闭Web终端服务...", file=sys.stderr)
            
            # 1. 关闭所有终端进程
            terminated_count = 0
            for session_id in list(self.terminal_manager.sessions.keys()):
                try:
                    await self.terminal_manager.kill_session(session_id)
                    terminated_count += 1
                    print(f"[INFO] 已终止终端: {session_id}", file=sys.stderr)
                except Exception as e:
                    print(f"[ERROR] 终止终端失败 {session_id}: {e}", file=sys.stderr)
            
            # 2. 通知所有客户端服务正在关闭
            await self._broadcast({
                "type": "server_shutdown",
                "message": "Web服务正在关闭，所有终端已终止，资源已释放。\nMCP服务继续运行，下次AI调用时会重新启动Web界面。"
            })
            
            # 3. 等待消息发送
            await asyncio.sleep(0.5)
            
            # 4. 关闭所有WebSocket连接
            ws_count = len(self.active_connections)
            for ws in list(self.active_connections):
                try:
                    await ws.close()
                except:
                    pass
            self.active_connections.clear()
            print(f"[INFO] 已关闭 {ws_count} 个WebSocket连接", file=sys.stderr)
            
            # 5. 清空所有会话数据
            session_count = len(self.terminal_manager.sessions)
            self.terminal_manager.sessions.clear()
            print(f"[INFO] 已清空 {session_count} 个终端会话", file=sys.stderr)
            
            # 6. 重置标志（通知MCP服务器）
            if self.shutdown_callback:
                try:
                    self.shutdown_callback()
                    print("[INFO] 已通知MCP服务器重置标志", file=sys.stderr)
                except Exception as e:
                    print(f"[ERROR] shutdown回调失败: {e}", file=sys.stderr)
            
            print(f"[SUCCESS] Web服务关闭完成！", file=sys.stderr)
            print(f"  - 终止终端: {terminated_count} 个", file=sys.stderr)
            print(f"  - 关闭连接: {ws_count} 个", file=sys.stderr)
            print(f"  - 清空会话: {session_count} 个", file=sys.stderr)
            print(f"  - MCP服务: 继续运行 ✅", file=sys.stderr)
            print(f"  - 下次调用: 将重新启动Web服务 🔄", file=sys.stderr)
            
            return {
                "success": True, 
                "message": f"Web服务已关闭，资源已释放。\n终止终端: {terminated_count} 个\nMCP服务继续运行，下次AI调用时会重新启动。"
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接"""
            await websocket.accept()
            self.active_connections.add(websocket)
            
            try:
                # 发送初始数据
                stats = self.terminal_manager.get_stats()
                sessions = self.terminal_manager.get_all_sessions()
                await websocket.send_json({
                    "type": "init",
                    "stats": stats,
                    "sessions": sessions
                })
                
                # 持续监听消息
                while True:
                    data = await websocket.receive_json()
                    
                    if data["type"] == "execute":
                        session_id = data["session_id"]
                        command = data["command"]
                        source = data.get("source", "ai")  # 默认AI，用户输入会标记为user
                        asyncio.create_task(
                            self._execute_and_broadcast(session_id, command, source)
                        )
                    
                    elif data["type"] == "interrupt":
                        # 处理中断信号（Ctrl+C）
                        session_id = data.get("session_id")
                        if session_id and session_id in self.terminal_manager.sessions:
                            session = self.terminal_manager.sessions[session_id]
                            if session.process and session.process.poll() is None:
                                try:
                                    import signal
                                    session.process.send_signal(signal.SIGINT)
                                except:
                                    session.process.kill()
                    
                    elif data["type"] == "create_session":
                        name = data.get("name")
                        session_id = self.terminal_manager.create_session(name=name)
                        await self._broadcast({
                            "type": "session_created",
                            "session_id": session_id
                        })
                    
                    elif data["type"] == "kill_session":
                        session_id = data["session_id"]
                        await self.terminal_manager.kill_session(session_id)
                        await self._broadcast({
                            "type": "session_killed",
                            "session_id": session_id
                        })
                    
                    elif data["type"] == "request_stats":
                        stats = self.terminal_manager.get_stats()
                        await websocket.send_json({
                            "type": "stats_update",
                            "stats": stats
                        })
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                print(f"WebSocket错误: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    async def _execute_and_broadcast(self, session_id: str, command: str, source: str = "ai"):
        """执行命令并广播结果"""
        try:
            # 通知开始执行（包含来源信息）
            await self._broadcast({
                "type": "command_started",
                "session_id": session_id,
                "command": command,
                "source": source  # 传递命令来源
            })
            
            # 执行命令
            stdout, stderr, returncode = await self.terminal_manager.execute_command(
                session_id, command
            )
            
            # 广播结果
            await self._broadcast({
                "type": "command_completed",
                "session_id": session_id,
                "command": command,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode
            })
            
        except Exception as e:
            await self._broadcast({
                "type": "command_error",
                "session_id": session_id,
                "error": str(e)
            })
    
    async def _broadcast(self, message: dict):
        """广播消息到所有WebSocket连接"""
        import sys
        msg_type = message.get('type', 'unknown')
        print(f"[广播] 类型:{msg_type}, 连接数:{len(self.active_connections)}", file=sys.stderr)
        
        if len(self.active_connections) == 0:
            print(f"[警告] 无WebSocket连接，消息被丢弃", file=sys.stderr)
            return
        
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                print(f"[广播] 成功发送 {msg_type}", file=sys.stderr)
            except Exception as e:
                print(f"[广播] 发送失败: {e}", file=sys.stderr)
                disconnected.add(connection)
        
        # 清理断开的连接
        self.active_connections -= disconnected
    
    def find_available_port(self, start_port: int = 8000, end_port: int = 9000) -> int:
        """查找可用端口"""
        import socket
        
        # 首先尝试常规端口
        for port in range(start_port, end_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    return port
            except OSError:
                continue
        
        # 如果常规端口都被占用，尝试高端口
        for port in range(50000, 60000):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    return port
            except OSError:
                continue
        
        raise RuntimeError("无法找到可用端口")
    
    async def start(self):
        """启动Web服务器"""
        # 保存当前事件循环
        self.loop = asyncio.get_running_loop()
        print(f"[DEBUG] 保存事件循环引用: {self.loop}")
        
        # 查找可用端口
        self.port = self.find_available_port()
        
        print(f"Web服务器启动在端口: {self.port}")
        print(f"访问地址: http://localhost:{self.port}")
        
        # 在后台线程中打开浏览器
        def open_browser():
            import time
            time.sleep(1)  # 等待服务器启动
            webbrowser.open(f"http://localhost:{self.port}")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # 启动服务器
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

