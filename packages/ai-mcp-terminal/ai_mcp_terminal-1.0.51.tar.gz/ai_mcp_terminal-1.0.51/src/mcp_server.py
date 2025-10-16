"""
MCP服务器 - 实现标准MCP协议

IMPORTANT FOR WINDOWS USERS:
This system ALWAYS prioritizes WSL bash over Git Bash on Windows.
When you specify shell_type="bash" or leave it unspecified, WSL bash is auto-selected FIRST.
WSL provides the best Unix command compatibility and performance on Windows.
Detection order: WSL bash > Git Bash > PowerShell > CMD
"""
import asyncio
import json
import sys
import threading
import time
import webbrowser
from datetime import datetime
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# 全局变量，用于跟踪是否需要强制重新加载
FORCE_RELOAD = True

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .terminal_manager import TerminalManager
    from .web_server import WebTerminalServer
except ImportError:
    from terminal_manager import TerminalManager
    from web_server import WebTerminalServer


class MCPTerminalServer:
    """MCP终端服务器"""
    
    def __init__(self):
        self.server = Server("ai-mcp-terminal")
        self.terminal_manager = TerminalManager()
        self.web_server = None
        self.web_server_started = False
        self.uvicorn_server = None  # 保存uvicorn server引用
        self.web_server_thread = None  # 保存Web服务器线程引用
        self._start_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._setup_handlers()
        
    def reset_web_server(self):
        """重置Web服务器状态（在shutdown时调用）"""
        print(f"[INFO] 开始重置Web服务器...", file=sys.stderr)
        
        # 停止uvicorn server释放端口
        if self.uvicorn_server:
            try:
                print(f"[INFO] 正在关闭uvicorn服务器，释放端口...", file=sys.stderr)
                # uvicorn server的shutdown需要在其事件循环中调用
                if self.web_server and self.web_server.loop:
                    import asyncio
                    # 在web服务器的事件循环中调度shutdown
                    asyncio.run_coroutine_threadsafe(
                        self.uvicorn_server.shutdown(),
                        self.web_server.loop
                    )
                    print(f"[INFO] uvicorn服务器shutdown已调度", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] 停止uvicorn失败: {e}", file=sys.stderr)
        
        # 重置状态
        self.web_server_started = False
        self.web_server = None
        self.uvicorn_server = None
        
        print(f"[SUCCESS] Web服务器状态已重置，端口已释放 ✅", file=sys.stderr)
    
    def start_web_server(self):
        """启动Web服务器（在后台线程）"""
        import sys
        print(f"[Web] start_web_server开始", file=sys.stderr)
        sys.stderr.flush()
        
        if self.web_server_started:
            print(f"[Web] Web服务器已启动，跳过", file=sys.stderr)
            sys.stderr.flush()
            return
        
        print(f"[Web] 创建WebTerminalServer实例...", file=sys.stderr)
        sys.stderr.flush()
        
        self.web_server = WebTerminalServer(self.terminal_manager)
        
        print(f"[Web] WebTerminalServer创建完成", file=sys.stderr)
        sys.stderr.flush()
        
        # 设置shutdown回调
        self.web_server.shutdown_callback = self.reset_web_server
        print(f"[Web] shutdown回调已设置", file=sys.stderr)
        sys.stderr.flush()
        
        def run_web_server():
            import uvicorn
            
            print(f"[WebThread] run_web_server线程开始", file=sys.stderr)
            sys.stderr.flush()
            
            # 创建新的事件循环用于这个线程
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 保存循环引用到web_server
            self.web_server.loop = loop
            print(f"[WebThread] 事件循环创建: {loop}", file=sys.stderr)
            sys.stderr.flush()
            
            # 同时设置到terminal_manager，用于线程安全的事件触发
            self.terminal_manager._web_server_loop = loop
            print(f"[WebThread] 事件循环已设置到terminal_manager", file=sys.stderr)
            sys.stderr.flush()
            
            port = self.web_server.find_available_port()
            self.web_server.port = port
            print(f"[WebThread] 端口已设置: {port}", file=sys.stderr)
            sys.stderr.flush()
            
            print(f"\n=== AI-MCP Terminal Web界面 ===", file=sys.stderr)
            print(f"Web界面地址: http://localhost:{port}", file=sys.stderr)
            print(f"您可以在此查看AI执行的所有终端命令", file=sys.stderr)
            print(f"===========================\n", file=sys.stderr)
            
            # 启动后打开浏览器
            def open_browser():
                time.sleep(2)
                webbrowser.open(f"http://localhost:{port}")
                print(f"[提示] 浏览器已自动打开Web界面", file=sys.stderr)
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            config = uvicorn.Config(
                self.web_server.app,
                host="0.0.0.0",
                port=port,
                log_level="error"  # 降低日志级别
            )
            server = uvicorn.Server(config)
            
            # 保存server引用到外部，以便shutdown时使用
            self.uvicorn_server = server
            
            loop.run_until_complete(server.serve())
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        self.web_server_thread = web_thread
        self.web_server_started = True
        
        # 不再阻塞等待，Web服务器在后台启动
        # time.sleep(2) 已移除，避免阻塞MCP
        print(f"[INFO] Web服务器线程已启动，正在后台初始化...", file=sys.stderr)
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools
            
            IMPORTANT FOR WINDOWS USERS:
            This system ALWAYS prioritizes WSL bash over Git Bash on Windows.
            When using shell_type="bash" or auto-detection, WSL bash is selected FIRST.
            WSL provides better Unix command compatibility and performance.
            Detection order: WSL bash > Git Bash > PowerShell > CMD
            """
            return [
                Tool(
                    name="create_session",
                    description="""WARNING: This is an inefficient single-operation tool. Use create_batch instead.

In 99% of cases, you should use create_batch, not this tool.

PROHIBITED scenarios (must avoid):
- Need multiple terminals: Use create_batch immediately
- Need to execute multiple commands: Use create_batch immediately
- System checks or status queries: Use create_batch immediately
- Concurrent task execution: Use create_batch immediately

ONLY allowed scenario:
- Need exactly 1 terminal and certain no others will be needed

Mandatory rules (violations will error):
1. Calling this tool more than once per conversation: Error! Use create_batch
2. Creating then immediately calling execute_command: Error! Use create_batch with initial_command
3. Creating then immediately querying status: Error!

Performance comparison:
- Create 3 terminals: create_batch is 3x faster
- Create 10 terminals: create_batch is 10x faster

Parameters:
- cwd: Working directory (required)
- initial_command: Command to execute immediately after creation (recommended)
- shell_type: Terminal type (OPTIONAL - leave unspecified to auto-select WSL on Windows)

IMPORTANT for AI: DO NOT specify shell_type parameter!
- Omitting shell_type → System auto-selects WSL bash on Windows (BEST)
- Specifying shell_type → Only when you need specific shell

Auto-detection priority (when shell_type NOT specified):
- Windows: WSL bash > Git Bash > PowerShell > CMD
- Linux/macOS: bash

Shell types (ONLY specify if you need specific shell):
1. Leave UNSPECIFIED (recommended) - Auto-selects WSL bash on Windows
2. shell_type="wsl" - Force WSL bash (Linux subsystem)
3. shell_type="bash" - Force Git Bash on Windows
4. shell_type="powershell" - Windows PowerShell (Windows-specific tasks)
5. shell_type="cmd" - Windows CMD (legacy only)

Usage recommendations for AI:
- RECOMMENDED: create_session(cwd=".", initial_command="ls")  // No shell_type, auto WSL
- ONLY IF NEEDED: create_session(cwd=".", shell_type="bash")  // Forces Git Bash
- AVOID: Specifying shell_type unless user explicitly requests it""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Session name (optional, auto-generated if not provided)"
                            },
                            "cwd": {
                                "type": "string",
                                "description": "REQUIRED: AI's current working directory where terminal will be created. Use os.getcwd() or project root"
                            },
                        "shell_type": {
                            "type": "string",
                            "description": "OPTIONAL - DO NOT specify this parameter! Leave unspecified to auto-select WSL bash on Windows (recommended). Only specify if you need a specific shell: 'wsl'(WSL bash), 'bash'(Git Bash), 'powershell'(PowerShell), 'cmd'(CMD). System auto-detects WSL bash first when omitted.",
                            "enum": ["wsl", "bash", "cmd", "powershell", "pwsh", "zsh", "fish", "sh"]
                        },
                            "initial_command": {
                                "type": "string",
                                "description": "Optional: Command to execute immediately after terminal creation. This merges create+execute into one step for efficiency"
                            }
                        },
                        "required": ["cwd"]
                    }
                ),
                Tool(
                    name="execute_command",
                    description="""WARNING: This is an inefficient single-operation tool. Use execute_batch or create_batch instead.

If you see keywords like "system info", "check", "get": Use create_batch immediately!

PROHIBITED scenarios (must avoid):
- Need to execute multiple commands: Use execute_batch or create_batch immediately
- System information queries (systeminfo/wmic/ipconfig/dxdiag etc): Use create_batch immediately
- Any batch operations: Use execute_batch immediately
- Calling this tool multiple times in one conversation: Use execute_batch immediately

ONLY allowed scenario:
- Execute exactly 1 command in 1 existing terminal, and 100% certain no other commands needed

Mandatory rules (violations will auto-error):
1. Calling this tool >1 time per conversation: Error! Use execute_batch
2. Execute then immediately call get_output: Error! Use cross-conversation query
3. System check tasks: Error! Use create_batch

Performance comparison:
- Execute 3 commands: execute_batch is 3x faster (and only 1 call)
- Execute 10 commands: execute_batch is 10x faster (and only 1 call)""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            }
                        },
                        "required": ["session_id", "command"]
                    }
                ),
                Tool(
                    name="broadcast_command",
                    description="""Execute same command concurrently across multiple terminals (asyncio.gather, true concurrency).

Concurrency performance:
- N terminals execute simultaneously, time ≈ 1 terminal
- NOT sequential execution

Use cases:
- Restart all services simultaneously
- Batch clear caches
- Unified dependency updates

Task dispatch strategy: Returns immediately, does not wait for completion""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Terminal session ID list (optional, broadcasts to all sessions if not provided)"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="execute_batch",
                    description="""Batch tool (recommended): Execute multiple commands concurrently.

Prioritize this tool (do not loop execute_command calls).

Key to true concurrency:
WARNING: Must use DIFFERENT terminals! Same terminal can only execute serially!

WRONG usage (all to same terminal, still serial):
execute_batch(commands=[
  {session_id: "sys", command: "cmd1"},  // All sys terminal
  {session_id: "sys", command: "cmd2"},  // Serial execution!
  {session_id: "sys", command: "cmd3"}
])

CORRECT usage (different terminals, true concurrency):
execute_batch(commands=[
  {session_id: "term1", command: "systeminfo"},
  {session_id: "term2", command: "wmic cpu"},
  {session_id: "term3", command: "ipconfig"}
])

Concurrency performance:
- Different terminals: True concurrency, 10 commands time ≈ 1 command
- Same terminal: Serial, 10 commands time = 10x time

Recommended workflow:
1. First use create_batch to create multiple terminals
2. Then use execute_batch to send commands to different terminals

Prerequisite: Terminals must already be created""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "session_id": {
                                            "type": "string",
                                            "description": "Terminal session ID"
                                        },
                                        "command": {
                                            "type": "string",
                                            "description": "Command to execute"
                                        }
                                    },
                                    "required": ["session_id", "command"]
                                },
                                "description": "Command list, each contains session_id and command"
                            }
                        },
                        "required": ["commands"]
                    }
                ),
                Tool(
                    name="create_batch",
                    description="""BEST TOOL: Use this immediately for system checks and concurrent tasks!

Batch tool (use this in 99% of scenarios): True concurrent execution

ABSOLUTELY recommended scenarios (MUST use this tool):
- System information queries (systeminfo/wmic/ipconfig/dxdiag etc): Use this!
- Any "check local data" or "get system info" requests: Use this!
- Need to execute multiple commands: Use this!
- Need concurrent execution: Use this!
- Create multiple terminals: Use this!

Why prioritize this tool:
- Create multiple terminals and execute commands at once (one call completes all tasks)
- Each terminal runs independently, true concurrency (not serial)
- 10-100x faster than looping create_session calls
- Single call, no loops needed

Concurrency performance:
- All terminals created + executed simultaneously (asyncio.gather + ThreadPoolExecutor)
- 10 terminals time ≈ 1 terminal (10x faster)
- 100 terminals time ≈ 1 terminal (100x faster)

Perfect example (get system info - common user request):
create_batch(sessions=[
  {name: "sys1", cwd: ".", initial_command: "systeminfo"},
  {name: "sys2", cwd: ".", initial_command: "wmic cpu get name"},
  {name: "sys3", cwd: ".", initial_command: "wmic os get caption"},
  {name: "sys4", cwd: ".", initial_command: "ipconfig /all"}
])
// 4 commands execute simultaneously, time ≈ 1 command!

DON'T do this (same terminal serial):
create_session(name: "sys")
execute_batch(commands=[
  {session_id: "sys", command: "cmd1"},  // Serial!
  {session_id: "sys", command: "cmd2"}
])

After creation: Reply to user immediately, end conversation

IMPORTANT for AI: DO NOT specify shell_type in session objects!
- Omitting shell_type → Auto-selects WSL bash on Windows (BEST)
- Example (RECOMMENDED):
  sessions=[
    {name: "sys1", cwd: ".", initial_command: "systeminfo"},  // No shell_type!
    {name: "sys2", cwd: ".", initial_command: "wmic cpu"}     // No shell_type!
  ]

Auto-detection priority (when shell_type NOT specified):
- Windows: WSL bash > Git Bash > PowerShell > CMD
- Linux/macOS: bash

Shell types (ONLY specify if you need specific shell):
1. Leave UNSPECIFIED (recommended) - Auto-selects WSL bash on Windows
2. shell_type="wsl" - Force WSL bash (Linux subsystem)
3. shell_type="bash" - Force Git Bash on Windows
4. shell_type="powershell" - Windows PowerShell (Windows-specific tasks)
5. shell_type="cmd" - Windows CMD (legacy only)

Usage recommendations for AI:
- RECOMMENDED: sessions=[{name:"x", cwd:".", initial_command:"ls"}]  // No shell_type
- ONLY IF NEEDED: sessions=[{name:"x", cwd:".", shell_type:"bash"}]  // Forces Git Bash
- AVOID: Adding shell_type unless user explicitly requests it""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Session name"
                                        },
                                        "cwd": {
                                            "type": "string",
                                            "description": "Working directory"
                                        },
                                            "shell_type": {
                                            "type": "string",
                                            "description": "OPTIONAL - DO NOT specify! Leave unspecified to auto-select WSL bash on Windows (recommended). Only specify if you need a specific shell: 'wsl'(WSL bash), 'bash'(Git Bash), 'powershell', 'cmd'. System auto-detects WSL bash first when omitted.",
                                            "enum": ["wsl", "bash", "cmd", "powershell", "pwsh", "zsh", "fish", "sh"]
                                        },
                                        "initial_command": {
                                            "type": "string",
                                            "description": "Command to execute immediately after creation"
                                        }
                                    },
                                    "required": ["name", "cwd", "initial_command"]
                                },
                                "description": "Session list, each contains name, cwd, optional shell_type and initial_command"
                            }
                        },
                        "required": ["sessions"]
                    }
                ),
                Tool(
                    name="get_all_sessions",
                    description="Get list and status of all terminal sessions",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_session_status",
                    description="""Get detailed status of specified terminal session (returns immediately).

Usage rules:
1. Call at most once per conversation
2. Show results after calling, end conversation
3. Do not call repeatedly in single conversation""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_output",
                    description="""WARNING: This is an inefficient single-operation tool! Use get_batch_output immediately!

Calling this tool more than once in single conversation: STOP immediately! Use get_batch_output!

PROHIBITED scenarios (must avoid):
- Need to get multiple terminal outputs: Use get_batch_output immediately
- System check tasks: Use get_batch_output immediately
- Call this tool multiple times in one conversation: Use get_batch_output immediately
- Loop query status: Absolutely prohibited! Use cross-conversation query!

ONLY allowed scenario:
- Query exactly 1 terminal's output, and 100% certain won't query other terminals

Mandatory rules (violations will auto-error):
1. Call this tool >1 time per conversation: Error! Use get_batch_output
2. Call then call get_output/check_completion again: Error! End conversation immediately
3. Loop query until command completes: Error! Use cross-conversation query

Performance comparison:
- Query 10 outputs: get_batch_output is 10x faster (and only 1 call)
- Query 100 outputs: get_batch_output is 100x faster (and only 1 call)

Auto-protection mechanism: Cumulative queries >=5 will auto-terminate process (exit_code: -999)
WARNING: Must end conversation immediately after calling! Do not continue querying!""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "lines": {
                                "type": "number",
                                "description": "Get last N lines of output (default 100 lines, effective when only_last_command=False)"
                            },
                            "only_last_command": {
                                "type": "boolean",
                                "description": "Performance optimization: Whether to get only last command output (default false). Recommend setting to true to avoid reading large history data"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_batch_output",
                    description="""BEST TOOL: Use this immediately to get multiple terminal outputs!

Batch tool (MUST use): Concurrently get multiple terminal outputs

ABSOLUTELY recommended scenarios (MUST use this tool):
- Need to get 2 or more terminal outputs: Use this!
- Result collection for system check tasks: Use this!
- Batch check service status: Use this!
- Need multiple get_output in one conversation: STOP immediately! Use this!

DON'T loop call get_output! Use this tool to get all at once!

Concurrency performance (optimized to 100 threads):
- Max 100 threads reading simultaneously (ThreadPoolExecutor)
- NOT sequential reading!
- 10 terminals time ≈ 1 terminal (10x faster)
- 100 terminals time ≈ 1 terminal (100x faster)

Example (get system info results):
get_batch_output(session_ids=["sys1", "sys2", "sys3", "sys4"])
// Get all results at once, only 1 call

After getting: Show results, end conversation immediately!

Default only_last_command=true, only returns last command output
WARNING: Not providing session_ids reads all terminals (auto-discovery)""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Terminal session ID list (optional, gets all terminal outputs if not provided)"
                            },
                            "only_last_command": {
                                "type": "boolean",
                                "description": "Whether to get only last command output (default true, performance optimization). Set to false to return more history"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="interrupt_command",
                    description="v2.0.3: Interrupt current command but keep terminal (like Ctrl+C). Terminal becomes idle state, can continue executing new commands. Recommended: Use when need to stop command but keep terminal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="interrupt_batch",
                    description="""Batch interrupt commands (ThreadPoolExecutor, true concurrency)

Concurrency performance (optimized):
- Max 100 threads interrupt simultaneously
- All terminals interrupt at once, not sequential
- 100 terminals time ≈ 1 terminal (100x faster)

Use cases:
- Batch stop stuck services
- Emergency interrupt all tasks
- Quick reset terminal states

Task dispatch strategy:
1. Interrupt all terminals at once
2. Show interrupt results
3. End conversation

CORRECT: Terminals kept, can continue use
WRONG: To delete terminals, use kill_batch""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Session ID list to interrupt"
                            }
                        },
                        "required": ["session_ids"]
                    }
                ),
                Tool(
                    name="kill_session",
                    description="Delete entire terminal session (including terminal itself). WARNING: This deletes the terminal, if you only want to stop command use interrupt_command",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_stats",
                    description="Get system statistics information, including memory usage, terminal count, etc",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                # v2.0 new tools
                Tool(
                    name="get_terminal_states",
                    description="v2.0: Get detailed states of all terminals, core tool for AI task scheduling. Returns each terminal's running state (idle/running/waiting_input/completed), working directory, last command, whether reusable, etc. AI can intelligently assign tasks to idle terminals based on this info",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Session ID list to query, null means query all terminals"
                            },
                            "include_environment": {
                                "type": "boolean",
                                "description": "Whether to include environment info (Node/Python version etc). Default false to improve performance. WARNING: Enabling adds 3 second delay",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="send_input",
                    description="v2.0: Send input to terminal, for responding to interactive commands (like npm init). When detect_interactions detects terminal waiting for input, AI uses this tool to send response",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "input_text": {
                                "type": "string",
                                "description": "Input text to send, remember to include newline \\n"
                            },
                            "echo": {
                                "type": "boolean",
                                "description": "Whether to echo input content in response, default true",
                                "default": True
                            }
                        },
                        "required": ["session_id", "input_text"]
                    }
                ),
                Tool(
                    name="detect_interactions",
                    description="v2.0: Detect which terminals are waiting for user input. Identifies common prompt patterns (package name:, version:, (y/n) etc), and returns suggestions. AI should periodically call this tool to respond to interactive commands",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Session ID list to check, null means check all terminals"
                            }
                        }
                    }
                ),
                # v2.1 new tools
                Tool(
                    name="check_completion",
                    description="""Check multiple terminals' completion status (returns immediately, no waiting, multi-threaded concurrency).
Returns each terminal's running status, exit code, execution duration.

Usage rules (MUST follow):
1. Call at most once per conversation
2. Show results to user immediately after calling, end conversation
3. If commands still running, tell user "still in progress, please ask later"
4. Do not call this tool repeatedly in single conversation
5. Do not loop query, let user wait

Performance advantage (optimized):
- Max 100 threads concurrent checking
- 100 terminals time ≈ 1 terminal (100x faster)
- 1000 terminals time ≈ 10 terminals (100x faster)

WARNING: Query count protection: Cumulative queries >=5 will auto-terminate process""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Session ID list to check, empty means check all sessions"
                            }
                        }
                    }
                ),
                Tool(
                    name="kill_batch",
                    description="""Batch delete terminals (ThreadPoolExecutor, true concurrency)

Concurrency performance (optimized):
- Max 100 threads delete simultaneously
- 100 terminals from 100 seconds to 1 second (100x faster)
- 1000 terminals from 1000 seconds to 10 seconds (100x faster)

Use cases:
- Batch cleanup completed tasks
- Quick reset all terminals
- Emergency resource release

Task dispatch strategy:
1. Delete all terminals at once
2. Show deletion results
3. End conversation

WARNING: Terminals deleted, cannot recover
CORRECT: If only want to stop commands, use interrupt_batch""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Session ID list to delete"
                            }
                        },
                        "required": ["session_ids"]
                    }
                ),
                # v1.0.2 full keyboard interaction support
                Tool(
                    name="send_keys",
                    description="v1.0.2: Send any key or text to terminal. Supports all keyboard keys: letters, numbers, symbols, function keys (F1-F12), control keys (Ctrl+X), arrow keys, etc. Can send single key or full string. Use cases: Interactive command input, command line editing, vim/nano operations, etc",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "keys": {
                                "type": "string",
                                "description": "Key name or text content. Key examples: 'UP', 'DOWN', 'CTRL_C', 'F1', 'Ctrl+C', 'ENTER', 'TAB' etc. Text examples: 'hello world', 'yes', '123' etc"
                            },
                            "is_text": {
                                "type": "boolean",
                                "description": "Whether to send as plain text. true=send text directly, false=parse as key. Default false",
                                "default": False
                            }
                        },
                        "required": ["session_id", "keys"]
                    }
                ),
                Tool(
                    name="send_text",
                    description="v1.0.2: Quick send text to terminal (convenience method of send_keys). Sends string directly, not parsed as key. Suitable for quick text input",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text content to send"
                            }
                        },
                        "required": ["session_id", "text"]
                    }
                ),
                Tool(
                    name="get_live_output",
                    description="v1.0.2: Get terminal's real-time output stream. Returns latest output content, supports specifying max lines. Suitable for monitoring long-running command output",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Terminal session ID"
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "Maximum lines to return, default 100",
                                "default": 100
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="batch_send_keys",
                    description="""Batch send keys (ThreadPoolExecutor, true concurrency)

Concurrency performance (optimized):
- Max 100 threads send simultaneously
- All terminals receive input at once
- 100 terminals time ≈ 1 terminal (100x faster)

Use cases:
- Batch respond to interactive commands
- Simultaneously confirm multiple prompts
- Concurrent input configuration info

Task dispatch strategy:
1. Send all keys at once
2. Show send results
3. End conversation

CORRECT: Supports key and text modes""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interactions": {
                                "type": "array",
                                "description": "Interaction list",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "session_id": {"type": "string"},
                                        "keys": {"type": "string"},
                                        "is_text": {"type": "boolean", "default": False}
                                    },
                                    "required": ["session_id", "keys"]
                                }
                            }
                        },
                        "required": ["interactions"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """调用工具"""
            import sys
            
            # 强制flush所有输出，避免缓冲区问题
            sys.stdout.flush()
            sys.stderr.flush()
            
            print(f"\n[MCP] ========== 工具调用开始 ==========", file=sys.stderr)
            sys.stderr.flush()
            print(f"[MCP] 工具名: {name}", file=sys.stderr)
            sys.stderr.flush()
            print(f"[MCP] 参数: {arguments}", file=sys.stderr)
            sys.stderr.flush()
            
            # 首次调用时启动Web服务器（异步，不阻塞）
            # 检查Web服务器是否真正可用
            web_server_exists = self.web_server is not None
            
            print(f"[MCP] Web服务器检查: started={self.web_server_started}, exists={web_server_exists}", file=sys.stderr)
            sys.stderr.flush()
            
            if not self.web_server_started:
                try:
                    print(f"[MCP] 首次调用，启动Web服务器...", file=sys.stderr)
                    sys.stderr.flush()
                    
                    self.start_web_server()
                    print(f"[MCP] Web服务器启动完成", file=sys.stderr)
                    sys.stderr.flush()
                except Exception as web_err:
                    print(f"[MCP] Web服务器启动失败: {web_err}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
                    # 继续执行，不因Web服务器失败而中断MCP
            else:
                print(f"[MCP] Web服务器已启动，跳过启动步骤", file=sys.stderr)
                sys.stderr.flush()
            
            try:
                if name == "create_session":
                    # 获取当前工作目录（AI的工作目录）
                    import os
                    cwd = arguments.get("cwd") or os.getcwd()
                    initial_command = arguments.get("initial_command")
                    shell_type_arg = arguments.get("shell_type")  # 获取用户指定的终端类型
                    
                    print(f"[MCP] create_session参数: cwd={cwd}, shell_type={shell_type_arg}, initial_command={initial_command}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    session_id = self.terminal_manager.create_session(
                        name=arguments.get("name"),
                        cwd=cwd,
                        shell_type=shell_type_arg  # 传递shell_type参数
                    )
                    
                    # 获取会话信息
                    session_info = self.terminal_manager.get_session_status(session_id)
                    shell_type = session_info.get('shell_type', 'unknown')
                    
                    web_url = f"http://localhost:{self.web_server.port}" if self.web_server else "Web服务器启动中..."
                    
                    # 根据Shell类型提供命令建议
                    shell_tips = {
                        'wsl': "WSL bash (Windows Subsystem for Linux)\nFull Linux environment: ls, pwd, cd, echo $USER, grep, curl, apt etc\nNative Linux performance, best Unix compatibility",
                        'bash': "Git Bash (Windows)\nUse Unix commands: ls, pwd, cd, echo $USER, grep, curl\nNote: Windows CMD commands need: cmd /c \"command\"",
                        'zsh': "Zsh shell\nUse Unix commands: ls, pwd, cd, echo $USER, grep, curl\nEnhanced auto-completion and plugin system",
                        'fish': "Fish shell\nUse Unix commands: ls, pwd, cd, echo $USER, grep, curl\nFriendly interactive shell",
                        'powershell': "PowerShell\nUse PowerShell commands: Get-ChildItem, Get-Location, $env:USERNAME\nSupports pipelines and object operations",
                        'pwsh': "PowerShell Core\nUse PowerShell Core commands: Get-ChildItem, Get-Location, $env:USERNAME\nCross-platform PowerShell",
                        'cmd': "Windows CMD\nUse Windows CMD commands: dir, echo %USERNAME%, findstr\nNote: Unix commands not available",
                        'sh': "Sh shell\nUse basic Unix commands: ls, pwd, cd, echo $USER",
                        'dash': "Dash shell\nUse basic Unix commands: ls, pwd, cd, echo $USER"
                    }
                    
                    tip = shell_tips.get(shell_type, "Unknown shell type, use commands with caution")
                    
                    # 如果提供了初始命令，立即执行
                    if initial_command:
                        print(f"[MCP] 检测到initial_command，立即执行: {initial_command}", file=sys.stderr)
                        sys.stderr.flush()
                        await self.terminal_manager.execute_command(
                            session_id, 
                            initial_command, 
                            source="ai"
                        )
                        
                        # Shell类型智能提示
                        shell_warning = ""
                        if shell_type == "bash" and "powershell" not in initial_command.lower() and "cmd" not in initial_command.lower():
                            shell_warning = "\n\nNOTE: This is Git Bash. If you need WSL bash, create a new terminal without specifying shell_type."
                        elif shell_type in ["powershell", "cmd"] and initial_command and any(cmd in initial_command for cmd in ["ls", "grep", "curl", "apt", "yum"]):
                            shell_warning = f"\n\nWARNING: Command '{initial_command}' looks like Unix command but terminal is {shell_type}.\nRECOMMENDATION: Create a new WSL/bash terminal for Unix commands instead of continuing here."
                        
                        result = {
                            "success": True,
                            "session_id": session_id,
                            "cwd": cwd,
                            "shell_type": shell_type,
                            "web_url": web_url,
                            "command_tips": tip,
                            "initial_command": initial_command,
                            "initial_command_status": "executing",
                            "message": f"""Terminal session created and command executing

Session Info:
  - Session ID: {session_id}
  - Shell Type: {shell_type}
  - Working Directory: {cwd}
  - Web Interface: {web_url}

Initial Command: {initial_command}
Status: Executing in background

Advantage: Create+Execute in one step, 50% faster!
Command output will display in real-time on Web interface.

Command Usage Tips:
{tip}{shell_warning}""",
                            "ai_optimization_hint": {
                                "🚨🚨🚨_URGENT": "立即停止使用create_session！改用create_batch！",
                                "warning": "你刚才使用了低效的单次工具！系统检查任务必须用批量工具！",
                                "mandatory_rule": "在单次对话中调用create_session>1次 = 错误！必须改用create_batch！",
                                "correct_tool": "create_batch",
                                "why_better": "一次性创建多个终端并执行命令，真并发，速度快10-100倍",
                                "example": "create_batch(sessions=[{name:'sys1',cwd:'.',initial_command:'systeminfo'},{name:'sys2',cwd:'.',initial_command:'wmic cpu'},{name:'sys3',cwd:'.',initial_command:'ipconfig'}])",
                                "performance_comparison": "3个终端: create_session需要3次调用+3倍耗时，create_batch只需1次调用+1倍耗时",
                                "next_action": "如果还需要创建终端 → 立即改用create_batch！不要再调用create_session！"
                            }
                        }
                    else:
                        result = {
                            "success": True,
                            "session_id": session_id,
                            "cwd": cwd,
                            "shell_type": shell_type,
                            "web_url": web_url,
                            "command_tips": tip,
                            "message": f"""✅ 终端会话已创建成功

📋 会话信息:
  - 会话ID: {session_id}
  - Shell类型: {shell_type}
  - 工作目录: {cwd}
  - Web界面: {web_url}

💡 命令使用建议:
{tip}

💡 提示: 下次可以使用initial_command参数在创建时就执行命令，减少MCP调用！
🌐 提示: 用户可在Web界面实时查看所有操作""",
                            "ai_optimization_hint": {
                                "🚨🚨🚨_URGENT": "立即停止使用create_session！改用create_batch！",
                                "warning": "你刚才使用了低效的单次工具！系统检查任务必须用批量工具！",
                                "mandatory_rule": "在单次对话中调用create_session>1次 = 错误！必须改用create_batch！",
                                "correct_tool": "create_batch",
                                "why_better": "一次性创建多个终端并执行命令，真并发，速度快10-100倍",
                                "example": "create_batch(sessions=[{name:'sys1',cwd:'.',initial_command:'systeminfo'},{name:'sys2',cwd:'.',initial_command:'wmic cpu'},{name:'sys3',cwd:'.',initial_command:'ipconfig'}])",
                                "performance_comparison": "3个终端: create_session需要3次调用+3倍耗时，create_batch只需1次调用+1倍耗时",
                                "next_action": "如果还需要创建终端 → 立即改用create_batch！不要再调用create_session！"
                            }
                        }
                
                elif name == "execute_command":
                    print(f"[DEBUG] execute_command开始", file=sys.stderr)
                    sys.stderr.flush()
                    
                    session_id = arguments["session_id"]
                    command = arguments["command"]
                    
                    print(f"[DEBUG] session_id={session_id}, command={command}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 执行命令（立即返回，不等待完成）
                    exec_result = await self.terminal_manager.execute_command(
                        session_id, command, source="ai"
                    )
                    
                    print(f"[DEBUG] exec_result={exec_result}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 检查exec_result是否为None
                    if exec_result is None:
                        print(f"[ERROR] execute_command返回None！", file=sys.stderr)
                        sys.stderr.flush()
                        result = {
                            "success": False,
                            "error": "execute_command returned None",
                            "session_id": session_id,
                            "command": command
                        }
                    else:
                        print(f"[DEBUG] 构建result", file=sys.stderr)
                        sys.stderr.flush()
                        
                        web_url = f"http://localhost:{self.web_server.port}" if self.web_server else ""
                        
                        # 确保exec_result可JSON序列化
                        safe_exec_result = {
                            "status": str(exec_result.get("status", "unknown")),
                            "session_id": str(exec_result.get("session_id", session_id)),
                            "command": str(exec_result.get("command", command)),
                            "message": str(exec_result.get("message", "")),
                        }
                        if "error" in exec_result:
                            safe_exec_result["error"] = str(exec_result["error"])
                        
                        result = {
                            "success": True,
                            "session_id": str(session_id),
                            "command": str(command),
                            "status": "executing",  # 正在执行中
                            "web_url": str(web_url),
                            "exec_result": safe_exec_result,
                            "message": f"""✅ 命令已发送到终端 {session_id}（后台执行，不阻塞AI对话）

📋 命令: {command}
🔄 状态: 后台执行中
🌐 实时输出: {web_url}

💡 您可以继续与AI对话，命令在后台运行。
   所有输出将实时显示在Web界面。""",
                            "ai_optimization_hint": {
                                "🚨🚨🚨_URGENT": "立即停止使用execute_command！改用execute_batch或create_batch！",
                                "warning": "你刚才使用了低效的单次工具！系统检查任务必须用批量工具！",
                                "mandatory_rule": "在单次对话中调用execute_command>1次 = 错误！必须改用execute_batch或create_batch！",
                                "correct_tool": "create_batch (推荐) 或 execute_batch",
                                "why_better": "一次性向多个终端发送命令，真并发，速度快10-100倍",
                                "example_best": "create_batch(sessions=[{name:'sys1',cwd:'.',initial_command:'systeminfo'},{name:'sys2',cwd:'.',initial_command:'wmic cpu'}])",
                                "example_alternative": "execute_batch(commands=[{session_id:'term1',command:'cmd1'},{session_id:'term2',command:'cmd2'}])",
                                "performance_comparison": "10个命令: execute_command需要10次调用+10倍耗时，create_batch只需1次调用+1倍耗时",
                                "next_action": "如果还需要执行命令 → 立即改用批量工具！不要再调用execute_command！"
                            }
                        }
                        
                        print(f"[DEBUG] result已构建: {result is not None}", file=sys.stderr)
                        sys.stderr.flush()
                
                elif name == "broadcast_command":
                    import sys
                    command = arguments["command"]
                    session_ids = arguments.get("session_ids")
                    
                    print(f"[DEBUG] broadcast_command call", file=sys.stderr)
                    sys.stderr.flush()
                    
                    if not session_ids:
                        session_ids = [s["session_id"] for s in self.terminal_manager.get_all_sessions()]
                        print(f"  Auto get session_ids: {session_ids}", file=sys.stderr)
                        sys.stderr.flush()
                    
                    # 真正的并发执行 - 使用 asyncio.gather
                    print(f"  Broadcasting to {len(session_ids)} terminals concurrently", file=sys.stderr)
                    sys.stderr.flush()
                    
                    tasks = [
                        self.terminal_manager.execute_command(sid, command, source="ai")
                        for sid in session_ids
                    ]
                    await asyncio.gather(*tasks)
                    
                    web_url = f"http://localhost:{self.web_server.port}" if self.web_server else ""
                    
                    result = {
                        "success": True,
                        "session_count": len(session_ids),
                        "session_ids": session_ids,
                        "command": command,
                        "status": "executing",  # 所有终端都在执行中
                        "web_url": web_url,
                        "message": f"""✅ 命令已广播到 {len(session_ids)} 个终端（后台并发执行）

📋 命令: {command}
📊 终端数: {len(session_ids)}
🔄 状态: 所有终端后台执行中
🌐 实时输出: {web_url}

💡 您可以继续与AI对话，命令在后台运行。
   所有终端的输出将实时显示在Web界面。"""
                    }
                    print(f"[DEBUG] broadcast_command result: {result}", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "execute_batch":
                    import sys
                    commands = arguments["commands"]
                    
                    print(f"[DEBUG] execute_batch call: {len(commands)} commands", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 验证所有会话是否存在
                    invalid_sessions = []
                    for cmd in commands:
                        sid = cmd["session_id"]
                        if sid not in self.terminal_manager.sessions:
                            invalid_sessions.append(sid)
                    
                    if invalid_sessions:
                        result = {
                            "success": False,
                            "error": f"以下会话不存在: {', '.join(invalid_sessions)}",
                            "invalid_sessions": invalid_sessions
                        }
                    else:
                        # 真正的并发执行 - 使用 asyncio.gather
                        print(f"  Executing {len(commands)} commands concurrently", file=sys.stderr)
                        sys.stderr.flush()
                        
                        tasks = [
                            self.terminal_manager.execute_command(
                                cmd["session_id"], 
                                cmd["command"], 
                                source="ai"
                            )
                            for cmd in commands
                        ]
                        results = await asyncio.gather(*tasks)
                        
                        web_url = f"http://localhost:{self.web_server.port}" if self.web_server else ""
                        
                        result = {
                            "success": True,
                            "executed_count": len(commands),
                            "commands": commands,
                            "status": "executing",
                            "web_url": web_url,
                            "message": f"""✅ 批量命令已并发执行到 {len(commands)} 个终端
    
📋 命令数: {len(commands)}
🔄 状态: 所有命令并发执行中
🌐 实时输出: {web_url}

💡 真正的并发执行：所有命令同时开始，互不等待。
   每个终端的输出将实时显示在Web界面。"""
                        }
                        print(f"[DEBUG] execute_batch result: {result}", file=sys.stderr)
                        sys.stderr.flush()
                
                elif name == "create_batch":
                    import sys
                    sessions = arguments["sessions"]
                    
                    print(f"[DEBUG] create_batch call: {len(sessions)} sessions", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 并发创建所有会话并执行初始命令
                    async def create_and_execute(session_info):
                        name = session_info["name"]
                        cwd = session_info["cwd"]
                        initial_command = session_info["initial_command"]
                        shell_type = session_info.get("shell_type")  # 获取可选的shell_type
                        
                        # 创建会话
                        session_id = self.terminal_manager.create_session(
                            name=name,
                            cwd=cwd,
                            shell_type=shell_type  # 传递shell_type
                        )
                        
                        # 立即执行初始命令
                        await self.terminal_manager.execute_command(
                            session_id,
                            initial_command,
                            source="ai"
                        )
                        
                        return {
                            "session_id": session_id,
                            "name": name,
                            "cwd": cwd,
                            "initial_command": initial_command,
                            "status": "executing"
                        }
                    
                    print(f"  Creating {len(sessions)} sessions concurrently with initial commands", file=sys.stderr)
                    sys.stderr.flush()
                    
                    tasks = [create_and_execute(s) for s in sessions]
                    created_sessions = await asyncio.gather(*tasks)
                    
                    web_url = f"http://localhost:{self.web_server.port}" if self.web_server else ""
                    
                    result = {
                        "success": True,
                        "created_count": len(created_sessions),
                        "sessions": created_sessions,
                        "web_url": web_url,
                        "message": f"""✅ 批量创建 {len(created_sessions)} 个终端并同时执行初始命令

📋 创建数量: {len(created_sessions)}
🚀 每个终端的初始命令都已开始执行
🔄 状态: 所有命令并发执行中
🌐 实时输出: {web_url}

💡 效率提升：
  - 旧方式：创建N个终端 + 执行N个命令 = 2N次MCP调用
  - 新方式：批量创建并执行 = 1次MCP调用
  - 提升：{len(created_sessions)*2}次调用 → 1次调用，效率提升{len(created_sessions)*200}%！

🎯 所有终端已同时创建并开始执行，真正的并发！"""
                    }
                    print(f"[DEBUG] create_batch result: created {len(created_sessions)} sessions", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "get_all_sessions":
                    print(f"[MCP] 开始执行get_all_sessions", file=sys.stderr)
                    sys.stderr.flush()
                    sessions = self.terminal_manager.get_all_sessions()
                    print(f"[MCP] 获取到{len(sessions)}个会话", file=sys.stderr)
                    sys.stderr.flush()
                    result = {
                        "success": True,
                        "sessions": sessions,
                        "count": len(sessions)
                    }
                    print(f"[MCP] get_all_sessions结果已准备", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "get_session_status":
                    session_id = arguments["session_id"]
                    status = self.terminal_manager.get_session_status(session_id)
                    
                    if status is None:
                        result = {
                            "success": False,
                            "error": f"会话 {session_id} 不存在"
                        }
                    else:
                        result = {
                            "success": True,
                            "status": status
                        }
                
                elif name == "get_output":
                    print(f"[MCP] 开始执行get_output", file=sys.stderr)
                    sys.stderr.flush()
                    session_id = arguments["session_id"]
                    lines = arguments.get("lines", 100)
                    only_last_command = arguments.get("only_last_command", False)
                    print(f"[MCP] 参数: session_id={session_id}, lines={lines}, only_last_command={only_last_command}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 检查会话是否存在
                    if session_id not in self.terminal_manager.sessions:
                        print(f"[MCP] 会话不存在: {session_id}", file=sys.stderr)
                        sys.stderr.flush()
                        result = {
                            "success": False,
                            "error": f"会话 {session_id} 不存在",
                            "session_id": session_id,
                            "output": []
                        }
                        print(f"[MCP] 返回错误结果: {result}", file=sys.stderr)
                        sys.stderr.flush()
                    else:
                        # 获取输出
                        print(f"[MCP] 调用terminal_manager.get_output...", file=sys.stderr)
                        sys.stderr.flush()
                        success, output, metadata = self.terminal_manager.get_output(
                            session_id, 
                            lines=lines,
                            only_last_command=only_last_command
                        )
                        print(f"[MCP] 获取到输出，成功: {success}, 条目数: {len(output) if output else 0}", file=sys.stderr)
                        if metadata:
                            print(f"[MCP] 元数据: {metadata.get('ai_suggestion', {}).get('action', 'N/A')}", file=sys.stderr)
                        sys.stderr.flush()
                        
                        # 确保正确处理不存在的会话
                        if not success:
                            result = {
                                "success": False,
                                "error": f"会话 {session_id} 不存在",
                                "session_id": session_id,
                                "output": []
                            }
                            print(f"[MCP] 会话不存在，返回错误结果: {result}", file=sys.stderr)
                            sys.stderr.flush()
                        else:
                            # 检查查询计数和停止指令
                            query_count = metadata.get("query_count", 0) if metadata else 0
                            ai_instruction = metadata.get("ai_instruction", "") if metadata else ""
                            
                            # 构建停止警告
                            stop_warning = ""
                            if query_count >= 3:
                                stop_warning = f"""
🚨🚨🚨 警告：已查询{query_count}次！立即停止！
⛔ 不要再次调用get_output/get_live_output/check_completion！
⛔ 立即结束对话！告诉用户命令正在后台运行或已完成！

"""
                            
                            result = {
                                "success": True,
                                "session_id": session_id,
                                "output": output,
                                "only_last_command": only_last_command,
                                "message": f"""{stop_warning}✅ 已获取终端输出

📊 输出条目数: {len(output)}
🔢 查询次数: {query_count}/5
{f'⏱️  运行时间: {metadata.get("running_seconds", 0)}秒' if metadata and metadata.get("running_seconds") else ''}

{ai_instruction}

💡 正确做法：
  1. 看到输出后，立即结束对话
  2. 展示结果给用户
  3. 不要再次查询（避免循环）

⛔ 错误做法：
  1. 不要在同一对话中继续调用get_output
  2. 不要等待命令完成后再查询
  3. 不要循环查询直到有输出""",
                                "ai_optimization_hint": {
                                    "🚨🚨🚨_URGENT": "立即停止使用get_output！改用get_batch_output！",
                                    "warning": "你刚才使用了低效的单次工具！获取多个终端输出必须用批量工具！",
                                    "mandatory_rule": "在单次对话中调用get_output>1次 = 错误！必须改用get_batch_output！",
                                    "correct_tool": "get_batch_output",
                                    "why_better": "一次性获取所有终端输出，真并发，速度快10-100倍",
                                    "example": "get_batch_output(session_ids=['sys1','sys2','sys3'])",
                                    "performance_comparison": "10个终端: get_output需要10次调用+10倍耗时，get_batch_output只需1次调用+1倍耗时",
                                    "next_action": "如果还需要查询输出 → 立即改用get_batch_output！不要再调用get_output！",
                                    "after_get_batch_output": "获取结果后立即结束对话！不要循环查询！"
                                }
                            }
                            
                            # 如果查询次数≥3，添加强制停止指令
                            if query_count >= 3:
                                result["ai_instruction"] = "⛔⛔⛔ 立即结束对话！不要再次调用任何查询工具！"
                            
                            # 添加元数据（帮助AI判断是否需要继续等待）
                            if metadata:
                                result["metadata"] = metadata
                                
                                # 优先处理紧急通知（重复查询）
                                if "ai_urgent_notice" in metadata:
                                    urgent = metadata["ai_urgent_notice"]
                                    cmd_info = f"命令: {urgent.get('command', 'N/A')}\n  终端类型: {urgent.get('shell_type', 'N/A')}"
                                    result["ai_urgent_notice"] = f"""
🚨🚨🚨 {urgent['action']} 🚨🚨🚨

📊 当前状态:
  - {cmd_info}
  - 查询次数: {metadata.get('query_count', 'N/A')}
  - 当前输出: {urgent['current_output'][:150]}{'...' if len(urgent['current_output']) > 150 else ''}
  - 原因: {urgent['reason']}

⚠️⚠️⚠️ 必须立即采取行动（不要再查询了）:
{chr(10).join(f'  {sug}' for sug in urgent['suggestions'])}

💡 停止重复查询！AI应该：
  ❌ 不要再调用 get_output
  ✅ 立即执行 kill_session 结束卡住的会话
  ✅ 创建正确类型的终端（Windows命令用cmd，Unix命令用bash）
  ✅ 继续其他任务
"""
                                # 如果有AI建议，添加友好的提示消息
                                elif "ai_suggestion" in metadata:
                                    suggestion = metadata["ai_suggestion"]
                                    severity = suggestion.get('severity', 'medium')
                                    
                                    # 根据严重性调整图标
                                    if severity == 'high':
                                        icon = "🚨"
                                        urgency = "【高优先级】"
                                    elif severity == 'medium':
                                        icon = "⚠️"
                                        urgency = "【中等优先级】"
                                    else:
                                        icon = "💡"
                                        urgency = "【提示】"
                                    
                                    result["ai_notice"] = f"""
{icon} {urgency} {suggestion['action']}

📊 运行状态:
  - 命令: {metadata.get('command', 'N/A')}
  - 运行时间: {metadata.get('running_seconds', 0)}秒
  - 输出长度: {metadata.get('output_length', 0)}字符

💡 建议的操作:
{chr(10).join(f'  • {opt}' for opt in suggestion['options'])}

原因: {suggestion['reason']}

🎯 后续步骤:
  1. 如果是错误的终端类型 → kill_session + 创建正确终端
  2. 如果服务已启动 → 继续其他操作
  3. 如果卡住 → kill_session + 重新尝试
"""
                            print(f"[MCP] 会话存在，返回输出结果", file=sys.stderr)
                            sys.stderr.flush()
                    
                    print(f"[MCP] get_output结果已准备", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "get_batch_output":
                    print(f"[MCP] 开始执行get_batch_output", file=sys.stderr)
                    sys.stderr.flush()
                    
                    session_ids = arguments.get("session_ids")
                    only_last_command = arguments.get("only_last_command", True)  # 默认为True，性能优化
                    
                    # 如果没有提供session_ids，获取所有会话
                    if not session_ids:
                        session_ids = [s["session_id"] for s in self.terminal_manager.get_all_sessions()]
                        print(f"[MCP] 未提供session_ids，自动获取所有: {session_ids}", file=sys.stderr)
                        sys.stderr.flush()
                    
                    print(f"[MCP] 批量获取{len(session_ids)}个终端输出，only_last_command={only_last_command}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 批量获取输出
                    outputs = self.terminal_manager.get_batch_output(
                        session_ids,
                        only_last_command=only_last_command
                    )
                    
                    # 统计
                    total_commands = sum(len(output) for output in outputs.values())
                    
                    result = {
                        "success": True,
                        "session_count": len(session_ids),
                        "total_commands": total_commands,
                        "only_last_command": only_last_command,
                        "outputs": outputs,
                        "message": f"""✅ 批量获取 {len(session_ids)} 个终端的输出

📊 统计:
  - 终端数: {len(session_ids)}
  - 命令总数: {total_commands}
  - 模式: {'仅最后一次命令' if only_last_command else '完整历史'}

💡 性能优化: 只读取最后一次命令的输出，避免传输大量历史数据。
   如需完整历史，设置 only_last_command=false"""
                    }
                    
                    print(f"[MCP] get_batch_output完成: {len(session_ids)}个终端, {total_commands}个命令", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "interrupt_command":
                    session_id = arguments["session_id"]
                    
                    result = self.terminal_manager.interrupt_command(session_id)
                    
                    if result.get("success"):
                        result["message"] = f"""✅ 命令已中断，终端保留

📋 终端: {session_id}
🔄 状态: 空闲（可以继续使用）
💡 终端没有被删除，可以执行新命令

⚡ 这类似于按下 Ctrl+C，停止当前命令但保留终端"""
                    else:
                        if "No running command" in result.get("error", ""):
                            result["message"] = f"""ℹ️ 终端 {session_id} 当前没有运行命令

终端状态: 空闲
💡 可以直接执行新命令"""
                        else:
                            result["message"] = f"""❌ 中断命令失败

错误: {result.get('error', 'Unknown error')}
💡 如需删除整个终端，请使用 kill_session"""
                
                elif name == "interrupt_batch":
                    import sys
                    session_ids = arguments["session_ids"]
                    
                    print(f"[DEBUG] interrupt_batch调用: sessions={session_ids}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    result = self.terminal_manager.interrupt_commands(session_ids)
                    
                    total = len(session_ids)
                    result["total"] = total
                    result["message"] = f"""✅ 批量中断完成

📊 中断统计:
  - 总数: {total}
  - 成功: {result['success_count']}
  - 无命令: {result['no_command_count']}
  - 失败: {result['failed_count']}

⚡ 性能: 并发执行，{total}个终端同时中断！
💡 所有终端保留，可以继续使用

详细结果见 results 字段"""
                    
                    print(f"[DEBUG] interrupt_batch完成: 成功{result['success_count']}/{total}", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "kill_session":
                    session_id = arguments["session_id"]
                    
                    # 使用并发版本（单个也走并发路径）
                    batch_result = self.terminal_manager.kill_sessions([session_id])
                    session_result = batch_result["results"].get(session_id, {})
                    success = session_result.get("success", False)
                    
                    result = {
                        "success": success,
                        "session_id": session_id,
                        "message": f"""✅ 终端 {session_id} 已删除

⚠️ 注意: 整个终端已被删除（不只是停止命令）
💡 如果只想停止命令但保留终端，请使用 interrupt_command""" if success else f"❌ 终端 {session_id} 不存在或已删除",
                        "error": session_result.get("error") if not success else None
                    }
                
                elif name == "get_stats":
                    import sys
                    print(f"[DEBUG] get_stats调用", file=sys.stderr)
                    
                    stats = self.terminal_manager.get_stats()
                    print(f"[DEBUG] stats结果: {stats}", file=sys.stderr)
                    
                    memory_check = self.terminal_manager.check_memory_and_suggest_cleanup()
                    print(f"[DEBUG] memory_check结果: {memory_check}", file=sys.stderr)
                    
                    result = {
                        "success": True,
                        "stats": stats,
                        "memory_check": memory_check
                    }
                    
                    # 如果需要清理，添加建议
                    if memory_check and memory_check.get("should_cleanup"):
                        result["warning"] = "内存使用率过高，建议清理终端"
                        result["cleanup_suggestions"] = memory_check.get("suggestions", [])
                    
                    print(f"[DEBUG] get_stats返回结果: {result}", file=sys.stderr)
                
                # v2.0 new tool handling
                elif name == "get_terminal_states":
                    import sys
                    session_ids = arguments.get("session_ids")
                    include_environment = arguments.get("include_environment", False)  # 默认False
                    
                    print(f"[DEBUG] get_terminal_states调用: session_ids={session_ids}, include_env={include_environment}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    try:
                        print(f"[DEBUG] 开始调用 terminal_manager.get_terminal_states", file=sys.stderr)
                        sys.stderr.flush()
                        
                        states = self.terminal_manager.get_terminal_states(
                            session_ids=session_ids,
                            include_environment=include_environment
                        )
                        
                        print(f"[DEBUG] terminal_manager.get_terminal_states返回", file=sys.stderr)
                        sys.stderr.flush()
                        
                        if states.get("success"):
                            result = states
                            result["message"] = f"""✅ 已获取 {states['summary']['total']} 个终端的状态信息

📊 状态统计:
  - 空闲: {states['summary']['idle']}
  - 运行中: {states['summary']['running']}
  - 等待输入: {states['summary']['waiting_input']}
  - 已完成: {states['summary']['completed']}

💡 AI使用建议:
  - can_reuse=true 的终端可以复用
  - state=waiting_input 的终端需要send_input响应
  - state=idle/completed 的终端可以立即执行新命令
  - state=running 的终端正忙，不要打扰"""
                        else:
                            result = {
                                "success": False,
                                "error": states.get("error", "Unknown error"),
                                "terminals": {},
                                "summary": states.get("summary", {})
                            }
                        
                        print(f"[DEBUG] get_terminal_states完成", file=sys.stderr)
                        sys.stderr.flush()
                    
                    except Exception as e:
                        print(f"[ERROR] get_terminal_states调用异常: {e}", file=sys.stderr)
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                        sys.stderr.flush()
                        result = {
                            "success": False,
                            "error": f"调用失败: {str(e)}",
                            "terminals": {},
                            "summary": {
                                "total": 0,
                                "idle": 0,
                                "running": 0,
                                "waiting_input": 0,
                                "completed": 0
                            }
                        }
                
                elif name == "send_input":
                    import sys
                    session_id = arguments["session_id"]
                    input_text = arguments["input_text"]
                    echo = arguments.get("echo", True)
                    
                    print(f"[DEBUG] send_input调用: session={session_id}, echo={echo}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    result = self.terminal_manager.send_input(
                        session_id=session_id,
                        input_text=input_text,
                        echo=echo
                    )
                    
                    if result.get("success"):
                        result["message"] = f"""✅ 已向终端 {session_id} 发送输入

📋 发送内容: {result.get('input_sent', '***')}
⏰ 时间戳: {result.get('timestamp')}

💡 提示: 使用 get_output 工具查看终端的后续响应"""
                    
                    print(f"[DEBUG] send_input完成: {result}", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "detect_interactions":
                    import sys
                    session_ids = arguments.get("session_ids")
                    
                    print(f"[DEBUG] detect_interactions调用: session_ids={session_ids}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    result = self.terminal_manager.detect_interactions(session_ids=session_ids)
                    
                    print(f"[DEBUG] detect_interactions返回: result={result}, type={type(result)}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    if result["count"] > 0:
                        result["message"] = f"""⚠️ 检测到 {result['count']} 个终端正在等待输入

📋 交互详情: 见interactions列表

💡 处理建议:
  1. 使用 send_input 工具发送响应
  2. 查看 suggestions.type 了解输入类型(text_input/yes_no/choice/password)
  3. 可以使用 suggestions.default_value 作为默认值"""
                    else:
                        result["message"] = "✅ 所有终端都在正常运行，没有等待输入的情况"
                    
                    print(f"[DEBUG] detect_interactions完成，最终result: {result}", file=sys.stderr)
                    print(f"[DEBUG] detect_interactions即将继续到return语句...", file=sys.stderr)
                    sys.stderr.flush()
                
                elif name == "check_completion":
                    import sys
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    session_ids = arguments.get("session_ids")
                    
                    # 如果没有指定，检查所有会话
                    if not session_ids:
                        session_ids = list(self.terminal_manager.sessions.keys())
                    
                    print(f"[DEBUG] check_completion调用: sessions={session_ids}, 使用多线程并发", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 多线程并发检查状态（非阻塞，立即返回）
                    sessions_status = {}
                    completed = []
                    running = []
                    idle = []
                    
                    def check_single_status(sid):
                        """检查单个终端状态"""
                        status = self.terminal_manager.get_session_status(sid)
                        if status:
                            return sid, {
                                "is_running": status.get("is_running", False),
                                "exit_code": status.get("last_exit_code"),
                                "current_command": status.get("current_command"),
                                "last_command": status.get("last_command"),
                                "duration": status.get("duration_seconds", 0)
                            }
                        return sid, None
                    
                    # 使用线程池并发检查（最多100线程，提升检查性能）
                    max_workers = min(100, max(10, len(session_ids)))
                    
                    print(f"[DEBUG] check_completion使用 {max_workers} 个线程并发检查", file=sys.stderr)
                    sys.stderr.flush()
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {executor.submit(check_single_status, sid): sid for sid in session_ids}
                        
                        for future in as_completed(futures):
                            try:
                                session_id, status = future.result()
                                if status:
                                    sessions_status[session_id] = status
                                    
                                    if status["is_running"]:
                                        running.append(session_id)
                                    elif status["exit_code"] is not None:
                                        completed.append(session_id)
                                    else:
                                        idle.append(session_id)
                            except Exception as e:
                                print(f"[check_completion] 检查 {session_id} 失败: {e}", file=sys.stderr)
                    
                    # 构建停止提示
                    stop_message = ""
                    if len(running) > 0:
                        stop_message = f"""
🚨 看到运行中的命令？立即结束对话！
⛔ 不要再次调用check_completion/get_output/get_live_output！
⛔ 告诉用户命令正在后台运行，等下次询问时再查询！

"""
                    
                    result = {
                        "success": True,
                        "total": len(session_ids),
                        "running": running,
                        "completed": completed,
                        "idle": idle,
                        "sessions": sessions_status,
                        "message": f"""{stop_message}📊 状态检查完成（多线程并发，非阻塞）

📈 统计:
  - 运行中: {len(running)}
  - 已完成: {len(completed)}
  - 空闲: {len(idle)}

⚡ 性能: {len(session_ids)}个终端并发检查，最快{max_workers}倍速度！

💡 正确做法：
  - 运行中: 立即结束对话，告诉用户命令正在后台运行
  - 已完成: 可以调用get_batch_output一次批量读取结果，然后结束对话
  - 空闲: 终端等待新命令

⛔ 错误做法：
  - 不要在同一对话中循环调用check_completion等待完成
  - 不要连续调用多次get_output查询同一终端
  - 不要阻塞对话等待命令完成

🎯 跨对话查询：等用户下次问"完成了吗"时再调用此工具""",
                        "ai_instruction": "查看状态后立即结束对话！不要循环查询！"
                    }
                    
                    print(f"[DEBUG] check_completion完成（并发）: running={len(running)}, completed={len(completed)}, idle={len(idle)}", file=sys.stderr)
                    sys.stderr.flush()
                
                # v2.1 new tool handling
                elif name == "kill_batch":
                    import sys
                    session_ids = arguments["session_ids"]
                    
                    print(f"[DEBUG] kill_batch调用: sessions={session_ids}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 使用统一的并发删除方法
                    result = self.terminal_manager.kill_sessions(session_ids=session_ids)
                    
                    total = len(session_ids)
                    result["total"] = total
                    result["message"] = f"""✅ 并发删除完成

📊 删除统计:
  - 总数: {total}
  - 成功: {result['success_count']}
  - 失败: {result['failed_count']}

⚡ 性能: 并发执行，{total}个终端同时删除！

💡 详细结果见 results 字段"""
                    
                    print(f"[DEBUG] kill_batch完成: 成功{result['success_count']}/{total}", file=sys.stderr)
                    sys.stderr.flush()
                
                # v1.0.2 full keyboard interaction support
                elif name == "send_keys":
                    session_id = arguments["session_id"]
                    keys = arguments["keys"]
                    is_text = arguments.get("is_text", False)
                    
                    result = self.terminal_manager.send_keys(session_id, keys, is_text)
                    
                    if result.get("success"):
                        result["message"] = f"""✅ 已发送到终端 {session_id}

📤 发送内容: {keys}
📝 类型: {'文本' if is_text else '按键'}

💡 终端已接收输入，可以继续发送更多内容或查看输出"""
                
                elif name == "send_text":
                    session_id = arguments["session_id"]
                    text = arguments["text"]
                    
                    result = self.terminal_manager.send_text(session_id, text)
                    
                    if result.get("success"):
                        result["message"] = f"""✅ 文本已发送到终端 {session_id}

📤 内容: {text}

💡 可以使用get_live_output查看终端响应"""
                
                elif name == "get_live_output":
                    session_id = arguments["session_id"]
                    max_lines = arguments.get("max_lines", 100)
                    
                    result = self.terminal_manager.get_live_output(session_id, max_lines=max_lines)
                    
                    # 检查查询次数保护
                    query_count = result.get("query_count", 0)
                    ai_must_stop = result.get("ai_must_stop", False)
                    warning = result.get("warning", "")
                    
                    if result.get("success"):
                        output_lines = result.get("output_lines", [])
                        is_running = result.get("is_running", False)
                        current_cmd = result.get("current_command", "无")
                        running_seconds = result.get("running_seconds", 0)
                        
                        # 构建消息
                        stop_warning = ""
                        if ai_must_stop or query_count >= 3:
                            stop_warning = f"""
🚨🚨🚨 警告：已查询{query_count}次！立即停止！
⛔ 不要再次调用get_live_output/get_output/check_completion！
⛔ 立即结束对话！告诉用户命令正在后台运行！

"""
                        
                        result["message"] = f"""{stop_warning}📺 实时输出 - {session_id}

🔄 状态: {'运行中' if is_running else '空闲'}
📋 当前命令: {current_cmd}
⏱️  运行时间: {running_seconds}秒
📊 输出行数: {len(output_lines)}
🔢 查询次数: {query_count}/5

{warning if warning else ''}

💡 正确做法：
  1. 看到这个输出后，立即结束对话
  2. 告诉用户命令正在后台运行
  3. 等用户下次询问时再查询（跨对话查询）

⛔ 错误做法：
  1. 不要在同一对话中继续调用查询工具
  2. 不要等待命令完成
  3. 不要循环查询"""
                        
                        # 如果查询次数≥3，添加强制停止指令
                        if ai_must_stop:
                            result["ai_instruction"] = "⛔⛔⛔ 立即结束对话！不要再次调用任何查询工具！"
                    else:
                        # 失败情况（可能是查询≥5次被自动终止）
                        error = result.get("error", "未知错误")
                        action_taken = result.get("action_taken", "")
                        ai_instruction = result.get("ai_instruction", "")
                        
                        result["message"] = f"""❌ 查询失败
                        
错误: {error}
{f'操作: {action_taken}' if action_taken else ''}

{ai_instruction if ai_instruction else ''}

💡 命令已超时或被终止，请检查Web界面查看详情"""
                
                elif name == "batch_send_keys":
                    interactions = arguments["interactions"]
                    
                    result = self.terminal_manager.batch_send_keys(interactions)
                    
                    total = result.get("total", 0)
                    success = result.get("success_count", 0)
                    failed = result.get("failed_count", 0)
                    
                    result["message"] = f"""✅ 批量发送完成

📊 统计:
  - 总数: {total}
  - 成功: {success}
  - 失败: {failed}

⚡ 所有终端并发接收输入

详细结果见 results 字段"""
                    
                    if result.get("success"):
                        mode = "新终端" if result["created_new"] else f"终端 {result['executed_in']}"
                        result["message"] = f"""✅ 链式执行成功

📝 执行流程:
  1. 等待终端: {result['waited_for']} ✓
  2. 执行命令: {result['command']}
  3. 执行位置: {mode}

🎯 命令已在后台执行，输出将在Web界面实时显示

💡 这是真正的自动化！AI无需手动等待和分步执行"""
                    else:
                        result["message"] = f"""❌ 链式执行失败

错误: {result.get('error', 'Unknown error')}

💡 建议: 检查wait_for_session_id是否存在，或增加timeout"""
                    
                    print(f"[DEBUG] execute_after_completion完成: success={result.get('success')}", file=sys.stderr)
                    sys.stderr.flush()
                
                else:
                    # 检查是否是已删除的阻塞式工具
                    if name == "wait_for_completion":
                        result = {
                            "success": False,
                            "error": "工具已删除：wait_for_completion（阻塞式等待）",
                            "reason": "此工具会阻塞AI对话，违反非阻塞设计原则",
                            "alternative": "check_completion",
                            "message": """❌ wait_for_completion 已删除

⚠️ 原因: 此工具会阻塞AI对话（最长300秒），影响用户体验和其他IDE

✅ 替代方案: 使用 check_completion 工具
  - 立即返回状态，不等待
  - 可以定期调用检查进度
  - 永不阻塞AI对话

💡 使用示例:
1. 执行命令: create_session(initial_command="npm install")
2. 立即响应用户（不等待）
3. 需要时查询: check_completion()
4. 查看输出: get_output()

🔄 请重启IDE以刷新工具列表"""
                        }
                    elif name == "wait_for_text":
                        result = {
                            "success": False,
                            "error": "工具已删除：wait_for_text（阻塞式等待文本）",
                            "reason": "此工具会阻塞AI对话，等待特定文本出现",
                            "alternative": "get_live_output 或 get_output",
                            "message": """❌ wait_for_text 已删除

⚠️ 原因: 此工具会阻塞AI对话（最长30秒），等待特定文本出现

✅ 替代方案: 使用非阻塞读取
1. get_live_output(session_id) - 获取实时输出
2. get_output(session_id) - 获取命令输出
3. 在输出中搜索需要的文本（AI自己判断）

💡 使用示例:
# 错误方式（阻塞）
wait_for_text(session_id="build", text="Happy hacking!", timeout=120)

# 正确方式（非阻塞）
# 1. 执行命令
create_session(name="build", initial_command="npx create-react-app my-app")

# 2. 立即响应用户（不等待）

# 3. 定期获取输出并检查
output = get_output(session_id="build")
# AI检查output中是否包含"Happy hacking!"

# 4. 如果包含，说明完成；如果不包含，继续其他任务

🔄 请重启IDE以刷新工具列表"""
                        }
                    elif name == "execute_after_completion":
                        result = {
                            "success": False,
                            "error": "工具已删除：execute_after_completion（阻塞式链式执行）",
                            "reason": "此工具会阻塞AI对话，违反非阻塞设计原则",
                            "alternative": "先执行命令A，使用check_completion检查，完成后执行命令B",
                            "message": """❌ execute_after_completion 已删除

⚠️ 原因: 此工具会阻塞AI对话，等待前置命令完成

✅ 替代方案: AI主动控制流程
1. 执行命令A
2. 定期 check_completion() 检查状态
3. A完成后执行命令B

💡 示例:
# 步骤1: 执行安装
create_session(name="install", initial_command="npm install")

# 步骤2: 响应用户（不等待）

# 步骤3: 检查状态
check_completion(session_ids=["install"])

# 步骤4: 完成后执行构建
execute_command(session_id="install", command="npm run build")

🔄 请重启IDE以刷新工具列表"""
                        }
                    else:
                        result = {
                            "success": False,
                            "error": f"未知工具: {name}"
                        }
                
                import sys
                print(f"\n[MCP] 工具 {name} 执行完成", file=sys.stderr)
                print(f"[MCP] 准备返回result: {result}", file=sys.stderr)
                
                # ===== 全局错误保护：确保永远返回有效结果 =====
                
                # 1. 确保result已定义
                if 'result' not in locals() or result is None:
                    print(f"[ERROR] result未定义或为None！工具: {name}", file=sys.stderr)
                    sys.stderr.flush()
                    result = {
                        "success": False,
                        "error": f"内部错误：工具 {name} 未正确设置返回值",
                        "tool": name,
                        "recovery": "系统已捕获错误并返回默认值",
                        "suggestion": "请重试或使用不同的参数"
                    }
                
                # 2. 验证result的类型
                if not isinstance(result, dict):
                    print(f"[ERROR] result不是字典类型！工具: {name}, 类型: {type(result)}, 值: {result}", file=sys.stderr)
                    sys.stderr.flush()
                    result = {
                        "success": False,
                        "error": f"内部错误：工具 {name} 返回了无效类型: {type(result)}",
                        "tool": name,
                        "recovery": "系统已将返回值转换为标准格式"
                    }
                
                # 3. 确保必要字段存在
                if "success" not in result:
                    print(f"[WARNING] result缺少success字段，自动添加！工具: {name}", file=sys.stderr)
                    sys.stderr.flush()
                    result["success"] = False
                
                # 4. 确保错误时有错误信息
                if not result.get("success") and "error" not in result:
                    print(f"[WARNING] 失败但缺少error字段，自动添加！工具: {name}", file=sys.stderr)
                    sys.stderr.flush()
                    result["error"] = f"工具 {name} 执行失败，但未提供详细错误信息"
                
                # 5. 添加调试信息（帮助定位问题）
                if not result.get("success"):
                    result["debug_info"] = {
                        "tool": name,
                        "arguments": arguments,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # 序列化JSON
                try:
                    print(f"[MCP] 开始JSON序列化...", file=sys.stderr)
                    sys.stderr.flush()
                    json_text = json.dumps(result, ensure_ascii=False, indent=2)
                    print(f"[MCP] JSON序列化成功，长度: {len(json_text)}", file=sys.stderr)
                    sys.stderr.flush()
                except Exception as json_err:
                    print(f"[ERROR] JSON序列化失败: {json_err}", file=sys.stderr)
                    print(f"[ERROR] result内容: {result}", file=sys.stderr)
                    json_text = json.dumps({
                        "success": False,
                        "error": f"JSON序列化失败: {str(json_err)}"
                    }, ensure_ascii=False, indent=2)
                
                response = [TextContent(
                    type="text",
                    text=json_text
                )]
                print(f"[MCP] 返回response，数量: {len(response)}", file=sys.stderr)
                print(f"[MCP] ========== 工具调用结束 ==========\n", file=sys.stderr)
                return response
                
            except asyncio.TimeoutError:
                # 超时错误（单独处理）
                import sys
                print(f"[ERROR] 工具执行超时: {name}", file=sys.stderr)
                sys.stderr.flush()
                
                error_result = {
                    "success": False,
                    "error": f"工具 {name} 执行超时",
                    "error_type": "TimeoutError",
                    "tool": name,
                    "recovery": "操作已超时但系统正常运行",
                    "suggestion": "请检查命令是否正确，或增加超时时间",
                    "debug_info": {
                        "arguments": arguments,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(error_result, ensure_ascii=False, indent=2)
                )]
                
            except KeyError as e:
                # 参数缺失错误
                import sys
                print(f"[ERROR] 工具参数缺失: {name}, 缺少参数: {e}", file=sys.stderr)
                sys.stderr.flush()
                
                error_result = {
                    "success": False,
                    "error": f"缺少必需参数: {str(e)}",
                    "error_type": "KeyError",
                    "tool": name,
                    "recovery": "系统已捕获参数错误",
                    "suggestion": f"请提供缺少的参数: {str(e)}",
                    "debug_info": {
                        "provided_arguments": list(arguments.keys()) if arguments else [],
                        "missing_parameter": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(error_result, ensure_ascii=False, indent=2)
                )]
                
            except ValueError as e:
                # 值错误（如会话不存在）
                import sys
                print(f"[ERROR] 工具参数值错误: {name}, 错误: {e}", file=sys.stderr)
                sys.stderr.flush()
                
                error_result = {
                    "success": False,
                    "error": str(e),
                    "error_type": "ValueError",
                    "tool": name,
                    "recovery": "系统已捕获值错误",
                    "suggestion": "请检查参数值是否正确（如会话ID是否存在）",
                    "debug_info": {
                        "arguments": arguments,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(error_result, ensure_ascii=False, indent=2)
                )]
                
            except Exception as e:
                # 通用异常捕获（兜底）
                import sys
                import traceback
                print(f"[ERROR] 工具执行异常: {name}", file=sys.stderr)
                print(f"[ERROR] 异常类型: {type(e).__name__}", file=sys.stderr)
                print(f"[ERROR] 异常信息: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                
                error_result = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool": name,
                    "recovery": "系统已捕获未知错误但保持运行",
                    "suggestion": "这是一个未预期的错误，请检查参数或重试",
                    "debug_info": {
                        "arguments": arguments,
                        "exception_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(error_result, ensure_ascii=False, indent=2)
                )]
    
    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """主函数"""
    server = MCPTerminalServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

