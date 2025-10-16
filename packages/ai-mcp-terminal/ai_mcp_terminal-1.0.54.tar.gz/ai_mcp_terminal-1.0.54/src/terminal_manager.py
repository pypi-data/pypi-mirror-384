"""
终端管理器 - 管理多个终端会话
"""
import asyncio
import os
import platform
import psutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import threading
import queue


class TerminalSession:
    """终端会话类"""
    
    def __init__(self, session_id: str, shell_type: str, cwd: str = None, project_root: str = None):
        self.session_id = session_id
        self.shell_type = shell_type
        
        # 工作目录优先级：
        # 1. 明确传递的 cwd（AI指定的目录）
        # 2. project_root（项目根目录）
        # 3. os.getcwd()（最后的备选）
        if cwd:
            self.cwd = os.path.abspath(cwd)
        elif project_root:
            self.cwd = project_root
        else:
            self.cwd = os.getcwd()
        
        # 不在这里验证目录是否存在，让命令执行时报错
        # 这样AI能看到错误并自己创建目录
        
        self.status = "idle"  # idle, running, completed, waiting_input
        self.created_at = datetime.now()
        self.last_command = None
        self.last_command_time = None
        self.last_completed_at = None  # 🆕 最后完成时间
        self.last_exit_code = None  # 🆕 最后退出码
        self.output_history = []
        self.current_output = ""  # 当前运行命令的实时输出缓存
        self.current_command = None  # 当前运行的命令
        self.current_command_start_time = None  # 🆕 当前命令开始时间
        self.process = None
        self.output_queue = queue.Queue()
        self.lock = threading.Lock()
        
        # 🆕 v1.0.52: 输出统计
        self.output_bytes = 0  # 输出字节数
        self.output_lines = 0  # 输出行数
        self.output_truncated = False  # 输出是否被截断
        self.encoding_used = "utf-8"  # 使用的编码
        self.raw_output_bytes = b""  # 原始输出字节（用于调试）
        self.execution_warnings = []  # 执行警告列表
        
        # 追踪get_output调用（用于检测AI重复查询）
        self.get_output_call_count = 0  # 对当前命令的查询次数
        self.last_output_length = 0  # 上次输出的长度
        
        # 🆕 v2.0: 交互检测
        self.waiting_input = False  # 是否等待输入
        self.last_prompt_line = None  # 最后一行输出（可能是提示）
        self.interaction_detected_at = None  # 检测到交互的时间
        
        # 🆕 v2.0: 环境信息缓存
        self.environment = {}  # 环境信息（node版本、python版本等）
        self.environment_checked_at = None  # 环境检查时间
        
    def get_info(self) -> dict:
        """获取会话信息"""
        info = {
            "session_id": self.session_id,
            "shell_type": self.shell_type,
            "cwd": self.cwd,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_command": self.last_command,
            "last_command_time": self.last_command_time.isoformat() if self.last_command_time else None,
            "is_alive": self.process is not None and self.process.poll() is None,
            "query_count": self.get_output_call_count,  # 🎯 查询次数
        }
        
        # 添加运行时长
        if self.current_command_start_time:
            running_seconds = (datetime.now() - self.current_command_start_time).total_seconds()
            info["running_seconds"] = round(running_seconds, 1)
        
        # 添加查询警告
        if self.get_output_call_count >= 3:
            info["query_warning"] = f"已查询{self.get_output_call_count}次，还剩{max(0, 5-self.get_output_call_count)}次将自动终止"
        
        return info


class TerminalManager:
    """终端管理器"""
    
    def _detect_command_shell(self, command: str) -> Optional[str]:
        """
        根据命令语法智能推断应该使用的 shell 类型
        
        Args:
            command: 命令字符串
            
        Returns:
            推断的 shell 类型，如果无法判断则返回 None
        """
        # PowerShell 特征
        powershell_patterns = [
            'Remove-Item', 'Get-', 'Set-', 'New-', 'Write-Host',
            '$env:', '$_', '-ErrorAction', '-Recurse', '-Force',
            'Select-Object', 'Where-Object', 'ForEach-Object'
        ]
        
        # Bash/Unix 特征
        bash_patterns = [
            'rm -', 'ls -', 'cd ', 'export ', 'grep ', 'sed ',
            'awk ', 'chmod ', 'chown ', './configure', 'make ',
            '&&', '||', '|', '>', '<', 'source ', '. '
        ]
        
        # CMD 特征
        cmd_patterns = [
            'dir ', 'copy ', 'del ', 'move ', 'type ',
            'cd /d', 'set ', 'echo off'
        ]
        
        # 检测 PowerShell
        if any(pattern in command for pattern in powershell_patterns):
            return 'powershell'
        
        # 检测 Bash
        if any(pattern in command for pattern in bash_patterns):
            return 'bash'
        
        # 检测 CMD
        if any(pattern in command for pattern in cmd_patterns):
            return 'cmd'
        
        return None
    
    def _parse_error(self, output: str, exit_code: int, command: str) -> dict:
        """
        智能解析命令错误并提供建议
        
        Args:
            output: 命令输出
            exit_code: 退出码
            command: 执行的命令
            
        Returns:
            包含错误分析和建议的字典
        """
        result = {
            "error_type": "unknown",
            "actual_status": "failed",
            "suggestions": [],
            "quick_fix": None
        }
        
        output_lower = output.lower()
        
        # PyPI 文件已存在（实际上是成功）
        if "file already exists" in output_lower and "pypi" in output_lower:
            result["error_type"] = "pypi_duplicate"
            result["actual_status"] = "success"
            result["message"] = "文件已成功上传到 PyPI（之前已上传过）"
            result["suggestions"] = ["访问 PyPI 页面确认版本已发布"]
            return result
        
        # 编码错误
        if "unicodeencodeerror" in output_lower or "gbk" in output_lower:
            result["error_type"] = "encoding"
            result["message"] = "编码错误：控制台不支持 UTF-8 字符"
            result["suggestions"] = [
                "在命令前添加: chcp 65001",
                "设置环境变量: $env:PYTHONIOENCODING='utf-8'",
                "使用 --disable-progress-bar 参数（如果是 twine）"
            ]
            result["quick_fix"] = "chcp 65001; $env:PYTHONIOENCODING='utf-8'; " + command
            return result
        
        # 语法错误（Shell 类型不匹配）
        if "syntax error" in output_lower or "command not found" in output_lower:
            detected_shell = self._detect_command_shell(command)
            if detected_shell:
                result["error_type"] = "shell_mismatch"
                result["message"] = f"命令看起来是 {detected_shell} 语法，但可能在错误的 shell 中执行"
                result["suggestions"] = [
                    f"创建一个 {detected_shell} 类型的终端",
                    f"使用 create_session(shell_type='{detected_shell}')"
                ]
                return result
        
        # 权限错误
        if "permission denied" in output_lower or "access denied" in output_lower:
            result["error_type"] = "permission"
            result["message"] = "权限不足"
            result["suggestions"] = [
                "使用管理员权限运行",
                "检查文件/目录权限"
            ]
            return result
        
        # 文件/目录不存在
        if "no such file" in output_lower or "cannot find" in output_lower:
            result["error_type"] = "not_found"
            result["message"] = "文件或目录不存在"
            result["suggestions"] = [
                "检查路径是否正确",
                "检查工作目录是否正确"
            ]
            return result
        
        # 网络错误
        if "connection" in output_lower and ("refused" in output_lower or "timeout" in output_lower):
            result["error_type"] = "network"
            result["message"] = "网络连接错误"
            result["suggestions"] = [
                "检查网络连接",
                "使用 execute_with_retry 自动重试"
            ]
            return result
        
        # 通用错误
        result["message"] = f"命令失败 (退出码: {exit_code})"
        result["suggestions"] = ["检查命令输出了解详细错误信息"]
        
        return result
    
    def _smart_decode(self, data: bytes, primary_encoding: str) -> str:
        """
        智能解码：尝试多种编码方式，避免出现乱码
        
        优先级策略：
        1. 优先尝试 UTF-8（大多数程序输出都是UTF-8，包括Node.js、Python、emoji等）
        2. 如果UTF-8失败，尝试 GBK（Windows系统命令）
        3. 最后尝试其他编码
        
        Args:
            data: 要解码的字节数据
            primary_encoding: 参考编码（用于确定备选编码列表）
        
        Returns:
            解码后的字符串
        """
        if not data:
            return ''
        
        # 🔧 修复：优先尝试UTF-8（适用于大多数程序输出）
        # 原因：Node.js/Python/npm等程序输出UTF-8，emoji也是UTF-8
        encodings_to_try = [
            'utf-8',      # ← 优先UTF-8（程序输出、emoji）
            'gbk',        # ← 次选GBK（Windows系统命令）
            'cp936',      # Windows简体中文
            'gb18030',    # GBK的超集
            'latin-1'     # 最后的备选，能解码任何字节
        ]
        
        # 去重，保持顺序
        seen = set()
        encodings_to_try = [x for x in encodings_to_try if not (x.lower() in seen or seen.add(x.lower()))]
        
        # 尝试每种编码
        for encoding in encodings_to_try:
            try:
                decoded = data.decode(encoding)
                # 如果解码成功且不包含replacement字符，就使用这个结果
                if '�' not in decoded:
                    return decoded
                # 如果包含replacement字符但这是最后一种编码，也返回
                if encoding == encodings_to_try[-1]:
                    return decoded
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 如果所有编码都失败（理论上不应该发生），使用errors='ignore'
        return data.decode('utf-8', errors='ignore')
    
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
        self.command_tracker = defaultdict(list)  # 追踪相同命令的执行
        self.lock = threading.Lock()
        self.memory_threshold = 85  # 内存阈值百分比（从95降到85更安全）
        self.session_threshold = 50  # 降低到50个终端就开始检查（原来是64）
        self.max_sessions = 100  # 硬性限制：最多100个终端
        self.session_idle_timeout = 3600  # 空闲终端超时时间（1小时）
        self.event_callbacks = defaultdict(list)  # 事件回调字典
        
        # 保存项目根目录（当前工作目录）- 所有终端的默认工作目录
        self.project_root = os.getcwd()
        print(f"[TerminalManager] 项目根目录: {self.project_root}", file=sys.stderr)
        
        # 启动智能清理线程（超过50个终端+内存不足时自动清理最老的）
        self._start_smart_cleanup_thread()
        
        # 注册退出时的清理处理
        import atexit
        atexit.register(self.cleanup_all_sessions)
        
    def get_preferred_shell(self) -> str:
        """智能获取首选Shell类型 - 优先bash，其次powershell，最后cmd
        
        环境变量支持：
        - AI_MCP_PREFERRED_SHELL: 强制指定shell（bash/powershell/cmd/zsh等）
        """
        import sys
        
        # 1. 优先检查环境变量强制指定
        env_shell = os.environ.get('AI_MCP_PREFERRED_SHELL', '').strip().lower()
        if env_shell:
            print(f"[ShellDetect] ✅ 环境变量指定: AI_MCP_PREFERRED_SHELL={env_shell}", file=sys.stderr)
            sys.stderr.flush()
            return env_shell
        
        system = platform.system().lower()
        
        print(f"[ShellDetect] 开始检测首选终端，系统: {system}", file=sys.stderr)
        sys.stderr.flush()
        
        if system == "windows":
            # Windows shell优先级：WSL bash → Git Bash → powershell → cmd
            shells_priority = [
                ("wsl-bash", [  # WSL bash检测（最高优先级）
                    r"C:\Windows\System32\bash.exe",  # WSL bash (系统路径)
                    "wsl.exe",  # WSL 命令
                ]),
                ("bash", [  # Git Bash检测
                    r"C:\Program Files\Git\bin\bash.exe",  # Git Bash
                    r"C:\Program Files (x86)\Git\bin\bash.exe",
                    os.path.expandvars(r"%PROGRAMFILES%\Git\bin\bash.exe"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe"),
                    os.path.expanduser(r"~\scoop\apps\git\current\bin\bash.exe"),  # Scoop安装
                    "bash",  # PATH中的bash（通常是Git Bash）
                ]),
                ("powershell", ["powershell"]),  # PowerShell（第三优先）
                ("pwsh", ["pwsh"]),  # PowerShell Core（第四优先）
                ("cmd", ["cmd"]),  # CMD（最后选择）
                ("zsh", ["zsh"]),  # 其他shell
                ("fish", ["fish"])
            ]
            
        elif system == "darwin":
            # macOS shell优先级：zsh → bash → fish → sh（macOS默认zsh）
            shells_priority = [
                ("zsh", ["zsh"]),
                ("bash", ["bash"]),
                ("fish", ["fish"]),
                ("sh", ["sh"])
            ]
            
        else:
            # Linux/Unix shell优先级：bash → zsh → fish → dash → sh（标准bash优先）
            shells_priority = [
                ("bash", ["bash"]),
                ("zsh", ["zsh"]),
                ("fish", ["fish"]),
                ("dash", ["dash"]),
                ("sh", ["sh"])
            ]
        
        # 检测第一个可用的shell - 按列表顺序检测，优先WSL，然后Git Bash
        for shell_type, shell_commands in shells_priority:
            print(f"[ShellDetect] 检测 {shell_type}...", file=sys.stderr)
            sys.stderr.flush()
            
            for cmd in shell_commands:
                # 不是路径的命令（如 "bash", "wsl.exe"），检查 PATH
                if not (os.path.sep in cmd or (cmd.endswith('.exe') and not cmd in ['wsl.exe', 'bash.exe'])):
                    print(f"[ShellDetect] 检查PATH: {cmd}", file=sys.stderr)
                    sys.stderr.flush()
                    if self._command_exists(cmd):
                        if shell_type == "wsl-bash":
                            print(f"[ShellDetect] ✅ 找到shell: wsl-bash (WSL Linux subsystem)", file=sys.stderr)
                            sys.stderr.flush()
                            # 设置环境变量标记使用WSL
                            os.environ['AI_MCP_WSL_DETECTED'] = '1'
                            return "wsl"  # 返回wsl让前端可以区分
                        else:
                            print(f"[ShellDetect] ✅ 找到shell: {shell_type} (PATH)", file=sys.stderr)
                            sys.stderr.flush()
                            return shell_type
                # 固定路径的命令，检查文件是否存在
                else:
                    print(f"[ShellDetect] 检查路径: {cmd}", file=sys.stderr)
                    sys.stderr.flush()
                    if os.path.exists(cmd):
                        if shell_type == "wsl-bash":
                            print(f"[ShellDetect] ✅ 找到shell: wsl-bash at {cmd} (WSL)", file=sys.stderr)
                            sys.stderr.flush()
                            os.environ['AI_MCP_WSL_DETECTED'] = '1'
                            return "wsl"
                        else:
                            print(f"[ShellDetect] ✅ 找到shell: {shell_type} at {cmd}", file=sys.stderr)
                            sys.stderr.flush()
                            return shell_type
                    else:
                        print(f"[ShellDetect] ❌ 路径不存在: {cmd}", file=sys.stderr)
                        sys.stderr.flush()
        
        # 默认返回
        print(f"[ShellDetect] ⚠️ 未找到bash/powershell，使用默认", file=sys.stderr)
        sys.stderr.flush()
        return "powershell" if system == "windows" else "bash"
    
    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            if platform.system().lower() == "windows":
                subprocess.run(["where", command], capture_output=True, check=True)
            else:
                subprocess.run(["which", command], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _get_shell_executable(self, shell_type: str) -> str:
        """获取Shell可执行文件路径"""
        system = platform.system().lower()
        
        # Windows特殊处理
        if system == "windows":
            if shell_type == "wsl":
                # WSL bash
                wsl_bash = r"C:\Windows\System32\bash.exe"
                if os.path.exists(wsl_bash):
                    print(f"[ShellDetect] 使用 WSL bash: {wsl_bash}", file=sys.stderr)
                    sys.stderr.flush()
                    return wsl_bash
                return "bash"  # 回退
            
            elif shell_type == "bash":
                # Git Bash路径
                git_bash_paths = [
                    r"C:\Program Files\Git\bin\bash.exe",
                    r"C:\Program Files (x86)\Git\bin\bash.exe"
                ]
                for path in git_bash_paths:
                    if os.path.exists(path):
                        print(f"[ShellDetect] 使用 Git Bash: {path}", file=sys.stderr)
                        sys.stderr.flush()
                        return path
                return "bash"  # 回退到PATH中的bash
            
            elif shell_type == "pwsh":
                return "pwsh"
            elif shell_type == "powershell":
                return "powershell"
            elif shell_type == "cmd":
                return "cmd"
        
        # Unix-like系统
        return shell_type  # zsh, bash, fish等直接使用命令名
    
    def register_callback(self, callback, event_type: str = 'default'):
        """注册事件回调"""
        self.event_callbacks[event_type].append(callback)
    
    def _trigger_event(self, event_type: str, data: dict):
        """触发事件（线程安全）"""
        import sys
        print(f"[DEBUG] Trigger event: {event_type}, data keys: {list(data.keys())}", file=sys.stderr)
        sys.stderr.flush()
        
        # 触发默认回调
        for callback in self.event_callbacks['default']:
            try:
                # 线程安全的事件触发：
                # 1. 首先尝试获取当前运行的事件循环（主线程）
                # 2. 如果没有，说明在后台线程中，需要使用run_coroutine_threadsafe
                import asyncio
                import threading
                
                try:
                    # 尝试获取当前线程的事件循环
                    loop = asyncio.get_running_loop()
                    # 如果成功，直接创建任务
                    loop.create_task(callback(event_type, data))
                    print(f"[DEBUG] Event {event_type} triggered in event loop", file=sys.stderr)
                except RuntimeError:
                    # 没有运行中的事件循环，说明在后台线程中
                    # 需要找到Web服务器的事件循环并调度任务
                    # 这个事件循环会在web_server中设置
                    if hasattr(self, '_web_server_loop') and self._web_server_loop:
                        print(f"[DEBUG] Event {event_type} via run_coroutine_threadsafe", file=sys.stderr)
                        sys.stderr.flush()
                        asyncio.run_coroutine_threadsafe(
                            callback(event_type, data),
                            self._web_server_loop
                        )
                    else:
                        print(f"[WARNING] Cannot trigger event {event_type}: no event loop", file=sys.stderr)
                        sys.stderr.flush()
                        
            except Exception as e:
                print(f"[ERROR] Event callback failed: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
    
    def create_session(self, name: str = None, shell_type: str = None, cwd: str = None) -> str:
        """创建新的终端会话（无数量限制，超过64个+内存不足时智能清理）"""
        import sys
        
        # 已移除会话数量限制 - 终端无上限
        # 超过64个终端+内存不足时，智能清理最老的已完成/空闲终端
        
        session_id = name or str(uuid.uuid4())[:8]
        
        if shell_type is None:
            shell_type = self.get_preferred_shell()
        
        # 获取shell可执行文件路径（用于日志）
        shell_exe = self._get_shell_executable(shell_type)
        
        with self.lock:
            session = TerminalSession(session_id, shell_type, cwd, self.project_root)
            self.sessions[session_id] = session
        
        dir_exists = os.path.exists(session.cwd)
        print(f"[INFO] Create session: {session_id}", file=sys.stderr)
        print(f"       Shell type: {shell_type}", file=sys.stderr)
        print(f"       Shell path: {shell_exe}", file=sys.stderr)
        print(f"       Working dir: {session.cwd}", file=sys.stderr)
        print(f"       Dir exists: {dir_exists}", file=sys.stderr)
        sys.stderr.flush()
        if not dir_exists:
            print(f"       [WARNING] Directory not found! AI should create it first", file=sys.stderr)
            sys.stderr.flush()
        
        # 触发会话创建事件
        self._trigger_event('session_created', {
            'session_id': session_id,
            'shell_type': shell_type,
            'shell_exe': shell_exe
        })
            
        return session_id
    
    async def execute_command(
        self, 
        session_id: str, 
        command: str, 
        timeout: int = None,
        source: str = "ai"
    ) -> dict:
        """在指定会话中执行命令（真正的异步非阻塞）
        
        立即返回，不等待命令完成！命令在后台执行，结果通过事件推送。
        """
        try:
            if session_id not in self.sessions:
                error_msg = f"会话 {session_id} 不存在"
                print(f"[ERROR] execute_command: {error_msg}", file=sys.stderr)
                sys.stderr.flush()
                return {
                    "status": "error",
                    "error": error_msg,
                    "session_id": session_id,
                    "recovery": "请先使用 create_session 创建会话"
                }
        
            session = self.sessions[session_id]
        
            # 🆕 v1.0.52: 智能检测命令与终端类型是否匹配
            detected_shell = self._detect_command_shell(command)
            shell_warning = None
            if detected_shell and detected_shell != session.shell_type:
                shell_warning = {
                    "type": "shell_mismatch",
                    "message": f"命令语法看起来是 {detected_shell}，但当前终端是 {session.shell_type}",
                    "suggestion": f"建议创建 {detected_shell} 类型的终端执行此命令",
                    "quick_fix": f"create_session(shell_type='{detected_shell}')"
                }
                print(f"[WARNING] Shell类型不匹配: 命令={detected_shell}, 终端={session.shell_type}", file=sys.stderr)
                sys.stderr.flush()
        
            # 检查是否需要终止旧的相同命令
            await self._check_duplicate_command(session, command)
            
            # 更新会话状态
            with session.lock:
                session.status = "running"
                session.last_command = command
                session.last_command_time = datetime.now()
                session.current_command_start_time = datetime.now()
                # 重置输出统计
                session.output_bytes = 0
                session.output_lines = 0
                session.output_truncated = False
                session.execution_warnings = []
                if shell_warning:
                    session.execution_warnings.append(shell_warning)
            
            # 触发命令开始事件
            self._trigger_event('command_started', {
                'session_id': session_id,
                'command': command,
                'source': source
            })
            
            # 在后台线程中执行命令（不等待完成！）
            def execute_in_background():
                result = self._execute_sync(session, command, timeout)
                
                # 执行完成后触发事件
                self._trigger_event('command_completed', {
                    'session_id': session_id,
                    'command': command,
                    'stdout': result[0],
                    'stderr': result[1],
                    'returncode': result[2]
                })
                    
                # 重置查询计数器
                with session.lock:
                    session.get_output_call_count = 0
                    session.last_output_length = 0
            
            # 启动后台线程，不等待
            thread = threading.Thread(target=execute_in_background, daemon=True)
            thread.start()
            
            # 立即返回，不等待命令完成
            result = {
                "status": "started",
                "session_id": session_id,
                "command": command,
                "message": "命令已在后台开始执行"
            }
            
            # 添加 shell 警告（如果有）
            if shell_warning:
                result["warning"] = shell_warning
            
            return result
                
        except Exception as e:
            # 全局异常捕获：永不卡住
            print(f"[ERROR] execute_command异常: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # 返回错误信息而不是抛出异常
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "session_id": session_id,
                "command": command,
                "recovery": "系统已捕获错误，终端会话仍可用"
            }
    
    def _execute_sync(
        self, 
        session: TerminalSession, 
        command: str, 
        timeout: int = None
    ) -> Tuple[str, str, int]:
        """同步执行命令"""
        try:
            # 获取shell可执行文件
            shell_exe = self._get_shell_executable(session.shell_type)
            
            # 根据shell类型构建命令
            if session.shell_type in ["bash", "zsh", "fish", "sh", "dash"]:
                # Unix-like shell使用 -c 参数
                shell_cmd = [shell_exe, "-c", command]
                
            elif session.shell_type in ["powershell", "pwsh"]:
                # PowerShell使用 -Command 参数
                shell_cmd = [shell_exe, "-NoLogo", "-NonInteractive", "-Command", command]
                
            elif session.shell_type == "cmd":
                # CMD使用 /c 参数
                shell_cmd = [shell_exe, "/c", command]
                
            else:
                # 未知shell类型，尝试使用通用方式
                shell_cmd = [shell_exe, "-c", command]
            
            # 智能检测编码
            import sys
            if platform.system().lower() == "windows":
                # Windows上根据shell类型选择编码
                if session.shell_type in ['bash', 'zsh', 'fish', 'sh']:
                    # Git Bash等Unix-like shell使用UTF-8
                    encoding = 'utf-8'
                else:
                    # CMD和PowerShell使用GBK
                    encoding = 'gbk'
            else:
                # Linux/macOS使用UTF-8
                encoding = 'utf-8'
            
            print(f"[encoding] session={session.session_id} shell={session.shell_type} encoding={encoding}", file=sys.stderr)
            
            # 设置环境变量禁用缓冲
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # 🆕 v1.0.52: Windows 下自动设置 UTF-8 环境变量
            if platform.system().lower() == "windows":
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                print(f"[encoding] 已设置 UTF-8 环境变量: PYTHONIOENCODING=utf-8, PYTHONUTF8=1", file=sys.stderr)
            
            # 执行命令（使用二进制模式，手动解码以确保正确处理编码）
            process = subprocess.Popen(
                shell_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # 无缓冲
                env=env,
                cwd=session.cwd
            )
            
            session.process = process
            
            # 设置当前命令和清空输出缓存
            with session.lock:
                session.current_command = command
                session.current_output = ""
                session.current_command_start_time = datetime.now()  # 🆕 记录开始时间
                session.get_output_call_count = 0  # 重置查询计数
                session.last_output_length = 0  # 重置输出长度
            
            # 实时读取输出的线程（使用更大的缓冲区，避免破坏多字节字符）
            stdout_lines = []
            stderr_lines = []
            
            def read_stdout():
                try:
                    buffer = b''
                    while True:
                        # 读取更大的块（1024字节），避免破坏多字节字符
                        chunk = process.stdout.read(1024)
                        if not chunk:
                            # 处理剩余buffer
                            if buffer:
                                try:
                                    line = self._smart_decode(buffer, encoding)
                                    stdout_lines.append(line)
                                    with session.lock:
                                        session.current_output += line
                                    for callback in self.event_callbacks['output_chunk']:
                                        try:
                                            callback({
                                                'session_id': session.session_id,
                                                'chunk': line,
                                                'stream': 'stdout'
                                            })
                                        except Exception as e:
                                            print(f"[ERROR] output_chunk callback: {e}")
                                except Exception as e:
                                    print(f"[ERROR] decode buffer: {e}")
                            break
                        
                        buffer += chunk
                        
                        # 按行分割并发送（保留最后的不完整行）
                        while b'\n' in buffer:
                            line_end = buffer.index(b'\n') + 1
                            line_bytes = buffer[:line_end]
                            buffer = buffer[line_end:]
                            
                            try:
                                line = self._smart_decode(line_bytes, encoding)
                            except Exception:
                                line = line_bytes.decode('utf-8', errors='replace')
                            
                            stdout_lines.append(line)
                            
                            # 累积到current_output
                            with session.lock:
                                session.current_output += line
                            
                            # 实时推送输出到WebSocket
                            for callback in self.event_callbacks['output_chunk']:
                                try:
                                    callback({
                                        'session_id': session.session_id,
                                        'chunk': line,
                                        'stream': 'stdout'
                                    })
                                except Exception as e:
                                    print(f"[ERROR] output_chunk callback: {e}")
                    
                    process.stdout.close()
                except Exception as e:
                    print(f"[ERROR] read_stdout failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            def read_stderr():
                try:
                    buffer = b''
                    while True:
                        # 读取更大的块（1024字节），避免破坏多字节字符
                        chunk = process.stderr.read(1024)
                        if not chunk:
                            # 处理剩余buffer
                            if buffer:
                                try:
                                    line = self._smart_decode(buffer, encoding)
                                    stderr_lines.append(line)
                                    with session.lock:
                                        session.current_output += line
                                    for callback in self.event_callbacks['output_chunk']:
                                        try:
                                            callback({
                                                'session_id': session.session_id,
                                                'chunk': line,
                                                'stream': 'stderr'
                                            })
                                        except Exception as e:
                                            print(f"[ERROR] output_chunk callback: {e}")
                                except Exception as e:
                                    print(f"[ERROR] decode buffer: {e}")
                            break
                        
                        buffer += chunk
                        
                        # 按行分割并发送（保留最后的不完整行）
                        while b'\n' in buffer:
                            line_end = buffer.index(b'\n') + 1
                            line_bytes = buffer[:line_end]
                            buffer = buffer[line_end:]
                            
                            try:
                                line = self._smart_decode(line_bytes, encoding)
                            except Exception:
                                line = line_bytes.decode('utf-8', errors='replace')
                            
                            stderr_lines.append(line)
                            
                            # 累积到current_output
                            with session.lock:
                                session.current_output += line
                            
                            # 实时推送错误输出到WebSocket
                            for callback in self.event_callbacks['output_chunk']:
                                try:
                                    callback({
                                        'session_id': session.session_id,
                                        'chunk': line,
                                        'stream': 'stderr'
                                    })
                                except Exception as e:
                                    print(f"[ERROR] output_chunk callback: {e}")
                    
                    process.stderr.close()
                except Exception as e:
                    print(f"[ERROR] read_stderr failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 启动实时读取线程
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待进程结束
            returncode = process.wait(timeout=timeout)
            
            # 给WMIC等命令额外的时间让输出流完成写入
            # 某些Windows命令在进程结束后仍在写入输出
            time.sleep(0.5)
            
            # 等待读取线程完全结束（设置超时防止卡死）
            # 对于WMIC等命令，它们的数据输出有延迟
            stdout_thread.join(timeout=5.0)
            stderr_thread.join(timeout=5.0)
            
            # 如果线程仍在运行，记录警告
            if stdout_thread.is_alive():
                print(f"[WARNING] stdout线程未在5秒内完成，可能输出被截断", file=sys.stderr)
            if stderr_thread.is_alive():
                print(f"[WARNING] stderr线程未在5秒内完成，可能输出被截断", file=sys.stderr)
            
            # 合并输出
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            # 保存输出
            output = stdout + stderr
            
            # 🆕 v1.0.52: 计算输出统计
            output_bytes = len(output.encode('utf-8'))
            output_lines = output.count('\n')
            
            with session.lock:
                # 更新输出统计
                session.output_bytes = output_bytes
                session.output_lines = output_lines
                session.encoding_used = encoding
                # 暂不实现截断功能，但预留标记
                session.output_truncated = False
                # 错误分类
                error_category = None
                error_description = None
                
                if returncode != 0:
                    stderr_lower = stderr.lower()
                    stdout_lower = stdout.lower()
                    combined_output = (stderr_lower + stdout_lower).strip()
                    
                    # 识别命令不存在错误
                    if 'command not found' in combined_output or 'not recognized' in combined_output or 'is not recognized as' in combined_output:
                        error_category = "COMMAND_NOT_FOUND"
                        cmd_name = command.split()[0] if command.split() else command
                        error_description = f"命令不存在：{cmd_name}"
                        
                        # 🆕 智能建议：检测是否是Windows特定命令在bash中执行
                        windows_commands = ['dir', 'cls', 'copy', 'move', 'del', 'rd', 'md', 'type', 'findstr', 'systeminfo', 'tasklist', 'ipconfig', 'netstat']
                        bash_commands = ['ls', 'clear', 'cp', 'mv', 'rm', 'rmdir', 'mkdir', 'cat', 'grep', 'uname', 'ps', 'ifconfig', 'ss']
                        
                        if cmd_name.lower() in windows_commands and session.shell_type == 'bash':
                            # Windows命令在bash中执行失败
                            history_item["ai_suggestion"] = {
                                "issue": f"Windows命令 '{cmd_name}' 在bash终端中不可用",
                                "solution": "需要在Windows终端（cmd/powershell）中执行",
                                "action": f"create_session(shell_type='cmd') 然后 execute_command('{command}')",
                                "reason": f"命令 '{cmd_name}' 是Windows特定命令，bash不支持"
                            }
                        elif cmd_name.lower() in bash_commands and session.shell_type in ['cmd', 'powershell']:
                            # Bash命令在Windows终端中执行失败
                            history_item["ai_suggestion"] = {
                                "issue": f"Unix/Linux命令 '{cmd_name}' 在{session.shell_type}终端中不可用",
                                "solution": "需要在bash终端中执行",
                                "action": f"create_session(shell_type='bash') 然后 execute_command('{command}')",
                                "reason": f"命令 '{cmd_name}' 是Unix/Linux命令，{session.shell_type}不支持"
                            }
                    
                    elif 'permission denied' in combined_output or 'access denied' in combined_output:
                        error_category = "PERMISSION_DENIED"
                        error_description = "权限不足，可能需要管理员权限"
                    elif 'no such file or directory' in combined_output:
                        error_category = "FILE_NOT_FOUND"
                        error_description = "文件或目录不存在"
                    elif 'syntax error' in combined_output or 'unexpected' in combined_output:
                        error_category = "SYNTAX_ERROR"
                        error_description = "命令语法错误，请检查命令格式"
                    elif returncode == 130:
                        error_category = "USER_INTERRUPTED"
                        error_description = "用户中断（Ctrl+C）"
                    elif returncode == 128:
                        error_category = "INVALID_ARGUMENT"
                        error_description = "无效的命令参数"
                    else:
                        error_category = "GENERAL_ERROR"
                        error_description = f"命令执行失败，退出码：{returncode}"
                    
                
                # 🆕 v1.0.52: 计算执行时间
                execution_time = (datetime.now() - session.current_command_start_time).total_seconds() if session.current_command_start_time else 0
                
                # 🆕 v1.0.52: 智能错误解析
                error_analysis = None
                if returncode != 0:
                    error_analysis = self._parse_error(output, returncode, command)
                
                history_item = {
                    "command": command,
                    "output": output,
                    "returncode": returncode,
                    "timestamp": datetime.now().isoformat(),
                    # 🆕 v1.0.52: 新增字段
                    "success": returncode == 0 or (error_analysis and error_analysis.get("actual_status") == "success"),
                    "execution_time": round(execution_time, 2),
                    "output_bytes": output_bytes,
                    "output_lines": output_lines,
                    "encoding_used": encoding,
                    "output_truncated": False
                }
                
                # 添加错误分类信息
                if error_category:
                    history_item["error_category"] = error_category
                
                # 🆕 v1.0.52: 添加智能错误解析
                if error_analysis:
                    history_item["error_analysis"] = error_analysis
                    history_item["error_description"] = error_description
                
                session.output_history.append(history_item)
                session.status = "idle" if returncode == 0 else "completed"
                session.process = None
                # 🆕 记录完成信息
                session.last_exit_code = returncode
                session.last_completed_at = datetime.now()
                session.waiting_input = False  # 重置交互标志
                # 清空当前命令和输出缓存
                session.current_command = None
                session.current_output = ""
                session.current_command_start_time = None
            
            return stdout, stderr, returncode
            
        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = "命令执行超时"
            with session.lock:
                # 保存错误到历史
                session.output_history.append({
                    "command": command,
                    "output": error_msg,
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat()
                })
                session.status = "idle"
                session.process = None
                session.last_exit_code = -1  # 🆕
                session.last_completed_at = datetime.now()  # 🆕
                session.current_command = None
                session.current_output = ""
                session.current_command_start_time = None  # 🆕
            return "", error_msg, -1
        except FileNotFoundError as e:
            # 工作目录不存在的特殊处理
            error_msg = f"Working directory not found: {session.cwd}\nPlease create it first or use cd to switch directory"
            print(f"[ERROR] Working directory not found: {session.cwd}")
            
            with session.lock:
                # 保存错误到历史
                session.output_history.append({
                    "command": command,
                    "output": error_msg,
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat()
                })
                session.status = "idle"
                session.process = None
                session.last_exit_code = -1  # 🆕
                session.last_completed_at = datetime.now()  # 🆕
                session.current_command = None
                session.current_output = ""
                session.current_command_start_time = None  # 🆕
            return "", error_msg, -1
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Command execution exception: {command}, error: {error_msg}")
            import traceback
            traceback.print_exc()
            
            with session.lock:
                # 保存错误到历史
                session.output_history.append({
                    "command": command,
                    "output": error_msg,
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat()
                })
                session.status = "idle"
                session.process = None
                session.last_exit_code = -1  # 🆕
                session.last_completed_at = datetime.now()  # 🆕
                session.current_command = None
                session.current_output = ""
                session.current_command_start_time = None  # 🆕
            return "", error_msg, -1
    
    async def _check_duplicate_command(self, session: TerminalSession, command: str):
        """检查并处理重复命令"""
        # 识别项目级别的命令（如 npm run, python manage.py 等）
        project_commands = ["npm run", "yarn", "python -m", "node", "npm start", "npm dev"]
        
        is_project_cmd = any(cmd in command for cmd in project_commands)
        
        if is_project_cmd:
            # 检查是否有相同的命令正在运行
            for sid, s in self.sessions.items():
                if s.status == "running" and s.last_command == command and s.cwd == session.cwd:
                    # 终止旧命令
                    await self.kill_session(sid)
                    break
    
    def interrupt_commands(self, session_ids: List[str]) -> dict:
        """
        批量并发中断多个终端的命令（v2.0.3新增）
        
        Args:
            session_ids: 要中断的会话ID列表
        
        Returns:
            中断结果字典
        """
        import sys
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        print(f"[InterruptBatch] 开始并发中断 {len(session_ids)} 个终端的命令", file=sys.stderr)
        sys.stderr.flush()
        
        results = {
            "success_count": 0,
            "failed_count": 0,
            "no_command_count": 0,
            "results": {}
        }
        
        def interrupt_single(session_id):
            """中断单个会话的命令"""
            try:
                result = self.interrupt_command(session_id)
                return session_id, result
            except Exception as e:
                return session_id, {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id
                }
        
        # 使用线程池并发中断（最多100线程，提升并发性能）
        max_workers = min(100, max(10, len(session_ids)))
        
        print(f"[InterruptBatch] 使用 {max_workers} 个线程并发中断", file=sys.stderr)
        sys.stderr.flush()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(interrupt_single, sid): sid for sid in session_ids}
            
            for future in as_completed(futures):
                try:
                    session_id, result = future.result()
                    if result.get("success"):
                        results["success_count"] += 1
                        results["results"][session_id] = {
                            "success": True,
                            "status": result.get("status", "idle")
                        }
                    elif "No running command" in result.get("error", ""):
                        results["no_command_count"] += 1
                        results["results"][session_id] = {
                            "success": True,
                            "status": "idle",
                            "message": "No running command"
                        }
                    else:
                        results["failed_count"] += 1
                        results["results"][session_id] = {
                            "success": False,
                            "error": result.get("error", "Unknown error")
                        }
                except Exception as e:
                    session_id = futures[future]
                    results["failed_count"] += 1
                    results["results"][session_id] = {
                        "success": False,
                        "error": str(e)
                    }
        
        print(f"[InterruptBatch] 完成: 成功{results['success_count']}, 无命令{results['no_command_count']}, 失败{results['failed_count']}", file=sys.stderr)
        sys.stderr.flush()
        
        return results
    
    def interrupt_command(self, session_id: str) -> dict:
        """
        中断当前命令但保留终端（Ctrl+C效果）
        
        Args:
            session_id: 会话ID
        
        Returns:
            操作结果
        """
        import sys
        
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        session = self.sessions[session_id]
        
        with session.lock:
            if session.process and session.process.poll() is None:
                try:
                    print(f"[Interrupt] 中断命令: {session_id}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 发送SIGINT（Ctrl+C）信号
                    parent = psutil.Process(session.process.pid)
                    
                    # 先尝试优雅终止子进程
                    for child in parent.children(recursive=True):
                        try:
                            child.terminate()  # SIGTERM
                        except:
                            pass
                    
                    # 终止主进程
                    parent.terminate()
                    
                    # 等待一小段时间
                    import time
                    time.sleep(0.5)
                    
                    # 如果还没结束，强制kill
                    if session.process.poll() is None:
                        for child in parent.children(recursive=True):
                            try:
                                child.kill()
                            except:
                                pass
                        parent.kill()
                    
                    # 更新状态为idle（可以继续使用）
                    session.status = "idle"
                    session.process = None
                    session.current_command = None
                    session.current_output = ""
                    session.last_exit_code = 130  # Ctrl+C的退出码
                    session.last_completed_at = datetime.now()
                    
                    print(f"[Interrupt] 命令已中断，终端变为空闲: {session_id}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "message": "命令已中断，终端现在空闲",
                        "status": "idle"
                    }
                except Exception as e:
                    print(f"[Interrupt] 中断失败: {e}", file=sys.stderr)
                    sys.stderr.flush()
                    return {
                        "success": False,
                        "error": str(e),
                        "session_id": session_id
                    }
            else:
                return {
                    "success": False,
                    "error": "No running command",
                    "session_id": session_id,
                    "message": "终端当前没有运行命令"
                }
    
    def _kill_session_sync(self, session_id: str) -> bool:
        """同步终止单个会话（内部方法）- 删除整个终端"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        with session.lock:
            if session.process and session.process.poll() is None:
                try:
                    # 终止进程及其子进程
                    parent = psutil.Process(session.process.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                except:
                    pass
                
            session.status = "completed"
            session.process = None
        
        # 从管理器中移除
        with self.lock:
            del self.sessions[session_id]
        
        return True
    
    async def kill_session(self, session_id: str) -> bool:
        """
        终止单个会话（兼容旧接口，内部调用并发版本）
        
        推荐使用 kill_sessions([session_id]) 获取更详细的结果
        """
        result = self.kill_sessions([session_id])
        return result["results"].get(session_id, {}).get("success", False)
    
    def kill_sessions(self, session_ids: List[str]) -> dict:
        """
        批量并发删除多个终端会话（v2.1新增）
        
        Args:
            session_ids: 要删除的会话ID列表
        
        Returns:
            删除结果字典
        """
        import sys
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import asyncio
        
        print(f"[KillBatch] 开始并发删除 {len(session_ids)} 个终端", file=sys.stderr)
        sys.stderr.flush()
        
        results = {
            "success_count": 0,
            "failed_count": 0,
            "results": {}
        }
        
        def kill_single(session_id):
            """删除单个会话的包装函数"""
            try:
                # 直接调用同步方法
                success = self._kill_session_sync(session_id)
                return session_id, success, None
            except Exception as e:
                return session_id, False, str(e)
        
        # 使用线程池并发删除（最多100线程，提升并发性能）
        max_workers = min(100, max(10, len(session_ids)))
        
        print(f"[KillBatch] 使用 {max_workers} 个线程并发删除", file=sys.stderr)
        sys.stderr.flush()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(kill_single, sid): sid for sid in session_ids}
            
            for future in as_completed(futures):
                try:
                    session_id, success, error = future.result()
                    if success:
                        results["success_count"] += 1
                        results["results"][session_id] = {"success": True}
                    else:
                        results["failed_count"] += 1
                        results["results"][session_id] = {
                            "success": False,
                            "error": error or "Session not found"
                        }
                except Exception as e:
                    session_id = futures[future]
                    results["failed_count"] += 1
                    results["results"][session_id] = {
                        "success": False,
                        "error": str(e)
                    }
        
        print(f"[KillBatch] 删除完成: 成功 {results['success_count']}/{len(session_ids)}", file=sys.stderr)
        sys.stderr.flush()
        
        return {
            "success": True,
            "total": len(session_ids),
            "success_count": results["success_count"],
            "failed_count": results["failed_count"],
            "results": results["results"]
        }
    
    async def execute_after_completion(
        self, 
        wait_for_session_id: str,
        command: str,
        target_session_id: Optional[str] = None,
        create_new: bool = False,
        new_session_config: Optional[dict] = None,
        timeout: float = 300
    ) -> dict:
        """
        等待指定终端完成后执行命令（链式执行，v2.1新增）
        
        Args:
            wait_for_session_id: 要等待完成的会话ID
            command: 要执行的命令
            target_session_id: 目标会话ID（如果为None且create_new=False，则使用wait_for_session_id）
            create_new: 是否创建新终端执行
            new_session_config: 新终端配置（如果create_new=True）
            timeout: 等待超时时间（秒）
        
        Returns:
            执行结果字典
        """
        import sys
        import time
        
        print(f"[ChainExec] 等待终端 {wait_for_session_id} 完成", file=sys.stderr)
        sys.stderr.flush()
        
        # 等待指定会话完成
        start_time = time.time()
        wait_result = self.wait_for_completion(
            session_ids=[wait_for_session_id],
            timeout=timeout,
            check_interval=0.5
        )
        
        # 检查结果
        if wait_for_session_id in wait_result["completed"]:
            print(f"[ChainExec] 终端 {wait_for_session_id} 已完成（成功）", file=sys.stderr)
            sys.stderr.flush()
        elif wait_for_session_id in wait_result["failed"]:
            print(f"[ChainExec] 终端 {wait_for_session_id} 已完成（失败）", file=sys.stderr)
            sys.stderr.flush()
            return {
                "success": False,
                "error": f"等待的终端 {wait_for_session_id} 执行失败",
                "exit_code": wait_result["results"].get(wait_for_session_id, {}).get("exit_code"),
                "waited_seconds": wait_result["elapsed_time"]
            }
        elif wait_for_session_id in wait_result["timeout"]:
            return {
                "success": False,
                "error": f"等待终端 {wait_for_session_id} 超时",
                "waited_seconds": timeout
            }
        else:
            return {
                "success": False,
                "error": f"终端 {wait_for_session_id} 不存在或状态未知",
                "waited_seconds": wait_result["elapsed_time"]
            }
        
        # 确定目标终端
        if create_new:
            print(f"[ChainExec] 创建新终端执行命令", file=sys.stderr)
            sys.stderr.flush()
            
            # 使用新终端配置或复制等待终端的配置
            if new_session_config:
                config = new_session_config
            else:
                wait_session = self.sessions.get(wait_for_session_id)
                if wait_session:
                    config = {
                        "cwd": wait_session.cwd,
                        "shell_type": wait_session.shell_type
                    }
                else:
                    config = {}
            
            # 创建新终端
            new_session_id = self.create_session(
                cwd=config.get("cwd"),
                shell_type=config.get("shell_type")
            )
            target_session_id = new_session_id
        else:
            # 使用现有终端
            if target_session_id is None:
                target_session_id = wait_for_session_id
            
            print(f"[ChainExec] 在终端 {target_session_id} 中执行命令", file=sys.stderr)
            sys.stderr.flush()
        
        # 执行命令（异步调用）
        exec_result = await self.execute_command(target_session_id, command)
        
        # 确保返回值可JSON序列化
        return {
            "success": True,
            "waited_for": str(wait_for_session_id),
            "executed_in": str(target_session_id),
            "created_new": bool(create_new),
            "command": str(command),
            "exec_result": {
                "status": exec_result.get("status"),
                "session_id": exec_result.get("session_id"),
                "command": exec_result.get("command"),
                "message": exec_result.get("message"),
                "error": exec_result.get("error")
            }
        }
    
    def get_session_status(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id].get_info()
    
    def get_all_sessions(self) -> List[dict]:
        """获取所有会话"""
        with self.lock:
            return [s.get_info() for s in self.sessions.values()]
    
    def get_output(self, session_id: str, lines: int = 100, only_last_command: bool = False) -> tuple[bool, List[dict], Optional[dict]]:
        """获取会话输出历史（包括运行中命令的实时输出）
        
        参数:
            session_id: 会话ID
            lines: 获取最近N行（only_last_command=False时生效）
            only_last_command: 是否只获取最后一次命令的输出（性能优化）
        
        返回: (success, output_list, metadata)
            metadata 包含运行状态信息，帮助AI判断是否需要继续等待
        """
        try:
            if session_id not in self.sessions:
                # 确保返回False和空列表（永不卡住）
                print(f"[WARNING] get_output: 会话 {session_id} 不存在", file=sys.stderr)
                return False, [], None
            
            session = self.sessions[session_id]
            
            # 使用超时锁防止死锁
            lock_acquired = session.lock.acquire(timeout=2.0)
            if not lock_acquired:
                print(f"[ERROR] get_output: 获取会话锁超时，可能死锁", file=sys.stderr)
                sys.stderr.flush()
                return False, [], {
                    "error": "获取会话锁超时",
                    "suggestion": "会话可能处于异常状态，建议使用 kill_session 重启"
                }
            
            try:
                metadata = None
                current_output_len = len(session.current_output)
                
                # 追踪重复查询
                if session.current_command:
                    # 检查输出是否有变化
                    if current_output_len == session.last_output_length:
                        session.get_output_call_count += 1
                    else:
                        session.get_output_call_count = 1
                    session.last_output_length = current_output_len
                
                if only_last_command:
                    # 只返回最后一次命令的输出
                    # 优先返回正在运行的命令，其次才是历史记录中最后完成的命令
                    if session.current_command:
                        # 有运行中的命令，返回它
                        output_list = [{
                            "command": session.current_command,
                            "output": session.current_output,
                            "returncode": None,  # 还在运行中，没有退出码
                            "timestamp": datetime.now().isoformat(),
                            "is_running": True  # 标记为运行中
                        }]
                        
                        # 检测长时间运行的命令
                        metadata = self._analyze_running_command(session)
                        
                    elif session.output_history:
                        # 没有运行中的命令，返回历史中最后完成的命令
                        output_list = [session.output_history[-1]]
                    else:
                        # 既没有运行中的命令，也没有历史记录
                        output_list = []
                else:
                    # 返回最近N行历史记录
                    output_list = list(session.output_history[-lines:])
                    
                    # 如果有正在运行的命令，追加到列表末尾
                    if session.current_command:
                        running_item = {
                            "command": session.current_command,
                            "output": session.current_output,
                            "returncode": None,  # 还在运行中，没有退出码
                            "timestamp": datetime.now().isoformat(),
                            "is_running": True  # 标记为运行中
                        }
                        output_list.append(running_item)
                        
                        # 检测长时间运行的命令
                        metadata = self._analyze_running_command(session)
                
                # 🎯 智能查询机制：AI作为调度器，不等待终端
                # 查询次数 1-2: 正常查询
                # 查询次数 3-4: 警告提醒
                # 查询次数 ≥5: 自动终止进程
                running_time = 0
                if session.last_command_time:
                    running_time = (datetime.now() - session.last_command_time).total_seconds()
                
                # 总是返回查询次数（让AI知道查了几次）
                if not metadata:
                    metadata = {}
                metadata["query_count"] = session.get_output_call_count
                metadata["running_seconds"] = round(running_time, 1)
                
                # 🔪 核心逻辑：查询≥5次，自动终止！
                if session.current_command and session.get_output_call_count >= 5:
                    # 立即终止进程
                    try:
                        if session.process and session.process.poll() is None:
                            if sys.platform == 'win32':
                                # Windows: 强制结束整个进程树
                                subprocess.run(['taskkill', '/F', '/T', '/PID', str(session.process.pid)], 
                                             capture_output=True, timeout=3)
                            else:
                                # Unix: 发送SIGKILL
                                os.killpg(os.getpgid(session.process.pid), signal.SIGKILL)
                            
                            session.process = None
                            session.status = "completed"
                            session.last_exit_code = -999  # 特殊退出码：自动终止
                            session.current_command = None
                            
                            # 保存输出到历史
                            if session.current_output:
                                session.output_history.append({
                                    "command": session.last_command,
                                    "output": session.current_output,
                                    "returncode": -999,
                                    "timestamp": datetime.now().isoformat()
                                })
                            session.current_output = ""
                            
                            print(f"[AUTO-KILL] 终端 {session_id} 查询超过5次，已自动终止", file=sys.stderr)
                    except Exception as e:
                        print(f"[AUTO-KILL] 终止失败: {e}", file=sys.stderr)
                    
                    # 返回终止信息
                    metadata["auto_killed"] = True
                    metadata["ai_urgent_notice"] = {
                        "status": f"🔪 已自动终止（累计查询{session.get_output_call_count}次）",
                        "last_output": session.current_output[-500:] if session.current_output else "(无输出)",
                        "analysis": {
                            "command": session.last_command,
                            "shell_type": session.shell_type,
                            "running_time": f"{round(running_time, 1)}秒",
                            "output_length": f"{current_output_len}字符",
                            "exit_code": -999,
                            "reason": "命令执行时间过长，自动终止"
                        },
                        "ai_next_actions": [
                            "✅ 分析最后输出，判断是否部分成功",
                            "✅ 继续执行其他并发任务",
                            "💡 如果失败，分析原因并尝试新方案",
                            "🚀 不要等待，立即分发下一个任务"
                        ]
                    }
                
                # ⚠️ 查询3-4次：警告（不终止）
                elif session.current_command and session.get_output_call_count >= 3:
                    metadata["repeated_query_warning"] = True
                    metadata["ai_notice"] = {
                        "warning": f"⚠️ 已查询{session.get_output_call_count}次（还剩{5-session.get_output_call_count}次将自动终止）",
                        "suggestion": "建议：继续执行其他任务，稍后再查询",
                        "current_progress": session.current_output[-200:] if session.current_output else "(无输出)"
                    }
                
                # 🎯 总是添加AI指令：结束对话！
                if not metadata:
                    metadata = {}
                metadata["ai_instruction"] = {
                    "rule": "🚨 立即结束对话！不要再次调用get_output/check_completion",
                    "action": "向用户展示当前结果，让用户等待，下次对话再查询"
                }
                
                return True, output_list, metadata
            finally:
                # 确保释放锁
                session.lock.release()
            
        except Exception as e:
            # 全局异常捕获：永不卡住
            print(f"[ERROR] get_output异常: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # 返回空结果而不是抛出异常
            return False, [], None
    
    def _analyze_running_command(self, session: TerminalSession) -> dict:
        """分析正在运行的命令，判断是否是长时间运行的命令
        
        返回元数据帮助AI决策
        """
        command = session.current_command
        output = session.current_output
        start_time = session.last_command_time
        
        if not start_time:
            return None
        
        # 计算运行时间
        running_seconds = (datetime.now() - start_time).total_seconds()
        
        # 识别长时间运行的命令模式
        long_running_patterns = [
            'npm run', 'yarn dev', 'yarn start', 'npm start', 'npm dev',
            'python manage.py runserver', 'rails server', 'flask run',
            'ng serve', 'next dev', 'vite', 'webpack serve',
            'ping -t', 'tail -f', 'watch', 'nodemon'
        ]
        
        is_long_running = any(pattern in command.lower() for pattern in long_running_patterns)
        
        # 构建元数据
        metadata = {
            "is_running": True,
            "running_seconds": round(running_seconds, 1),
            "command": command,
            "output_length": len(output),
            "is_likely_long_running": is_long_running,
        }
        
        # 根据情况给出建议（按优先级）
        
        # 高优先级：10秒无输出（可能卡住）
        if running_seconds > 10 and len(output) == 0:
            metadata["ai_suggestion"] = {
                "action": "命令已运行10秒但无任何输出，极可能卡住",
                "options": [
                    "使用 kill_session 结束这个会话",
                    "创建新会话重新尝试",
                    "检查命令是否正确",
                    "如果是Windows命令，创建对应的终端类型（cmd/powershell）"
                ],
                "reason": f"命令已运行 {round(running_seconds)}秒但没有任何输出",
                "severity": "high"
            }
        # 中优先级：长时间运行服务
        elif is_long_running and running_seconds > 5:
            metadata["ai_suggestion"] = {
                "action": "已获取到当前输出，这是一个持续运行的服务",
                "options": [
                    "如果输出显示服务已启动，可以继续其他操作",
                    "如果需要停止服务，使用 kill_session 工具",
                    "如果需要在同一目录执行其他命令，创建新的终端会话"
                ],
                "reason": f"命令已运行 {round(running_seconds)}秒，包含服务启动关键词",
                "severity": "medium"
            }
        # 低优先级：超长运行
        elif running_seconds > 30:
            metadata["ai_suggestion"] = {
                "action": "命令运行时间较长",
                "options": [
                    "如果输出看起来正常，可以继续等待",
                    "如果看起来卡住，使用 kill_session",
                    "创建新终端继续其他操作"
                ],
                "reason": f"命令已运行 {round(running_seconds)}秒",
                "severity": "low"
            }
        
        return metadata
    
    def get_all_outputs(self, only_last_command: bool = True) -> dict:
        """一次性并发获取所有终端的输出（超级便捷！）
        
        参数:
            only_last_command: 是否只获取最后一次命令的输出（默认True）
        
        返回: {session_id: output_list} 的字典
        """
        with self.lock:
            session_ids = list(self.sessions.keys())
        
        if not session_ids:
            return {}
        
        return self.get_batch_output(session_ids, only_last_command)
    
    def get_batch_output(self, session_ids: List[str], only_last_command: bool = True) -> dict:
        """批量获取多个会话的输出（真正的多线程并发）
        
        参数:
            session_ids: 会话ID列表
            only_last_command: 是否只获取最后一次命令的输出（默认True，性能优化）
        
        返回: {session_id: output_list} 的字典
        """
        import sys
        from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
        
        print(f"[BatchOutput] 开始并发读取 {len(session_ids)} 个终端的输出", file=sys.stderr)
        sys.stderr.flush()
        
        results = {}
        
        # 定义单个读取任务（带超时和错误保护）
        def read_single_output(session_id):
            try:
                print(f"[BatchOutput] 读取终端 {session_id}", file=sys.stderr)
                sys.stderr.flush()
                success, output, metadata = self.get_output(session_id, only_last_command=only_last_command)
                print(f"[BatchOutput] 终端 {session_id} 读取完成，success={success}, items={len(output) if output else 0}", file=sys.stderr)
                sys.stderr.flush()
                return session_id, success, output, metadata
            except Exception as e:
                print(f"[BatchOutput] 读取 {session_id} 异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                return session_id, False, [], None
        
        # 使用线程池并发读取（最多100线程，提升读取性能）
        max_workers = min(100, max(10, len(session_ids)))
        
        print(f"[BatchOutput] 使用 {max_workers} 个线程并发读取", file=sys.stderr)
        sys.stderr.flush()
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                print(f"[BatchOutput] 提交 {len(session_ids)} 个任务到线程池", file=sys.stderr)
                sys.stderr.flush()
                futures = {executor.submit(read_single_output, sid): sid for sid in session_ids}
                
                # 收集结果（带超时：每个任务最多10秒）
                print(f"[BatchOutput] 开始收集结果", file=sys.stderr)
                sys.stderr.flush()
                
                completed_count = 0
                for future in as_completed(futures, timeout=30):  # 总超时30秒
                    try:
                        session_id, success, output, metadata = future.result(timeout=10)  # 单个任务超时10秒
                        completed_count += 1
                        print(f"[BatchOutput] [{completed_count}/{len(session_ids)}] {session_id}: success={success}", file=sys.stderr)
                        sys.stderr.flush()
                        if success:
                            results[session_id] = output
                        else:
                            results[session_id] = []
                    except TimeoutError:
                        session_id = futures[future]
                        print(f"[BatchOutput] 读取 {session_id} 超时，跳过", file=sys.stderr)
                        sys.stderr.flush()
                        results[session_id] = []
                    except Exception as e:
                        session_id = futures[future]
                        print(f"[BatchOutput] 读取 {session_id} 失败: {e}", file=sys.stderr)
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                        sys.stderr.flush()
                        results[session_id] = []
        except TimeoutError:
            print(f"[BatchOutput] ⚠️ 批量读取超时（>30秒），返回已收集的结果", file=sys.stderr)
            sys.stderr.flush()
            # 为未完成的会话添加空结果
            for sid in session_ids:
                if sid not in results:
                    results[sid] = []
        except Exception as e:
            print(f"[BatchOutput] ❌ 批量读取失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # 返回空结果而不是崩溃
            for sid in session_ids:
                if sid not in results:
                    results[sid] = []
        
        print(f"[BatchOutput] 并发读取完成，成功: {len([r for r in results.values() if r])}/{len(session_ids)}", file=sys.stderr)
        sys.stderr.flush()
        
        return results
    
    def get_memory_usage(self) -> dict:
        """获取内存使用情况"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
    
    def check_memory_and_suggest_cleanup(self) -> dict:
        """检查内存并提供清理建议"""
        memory = self.get_memory_usage()
        suggestions = []
        
        if memory["percent"] >= self.memory_threshold:
            # 内存超过阈值，提供清理建议
            idle_sessions = []
            running_sessions = []
            
            for sid, session in self.sessions.items():
                if session.status == "idle" or session.status == "completed":
                    idle_sessions.append(sid)
                elif session.status == "running":
                    running_sessions.append(sid)
            
            if idle_sessions:
                suggestions.append({
                    "type": "kill_idle",
                    "message": f"建议清除 {len(idle_sessions)} 个空闲终端",
                    "session_ids": idle_sessions
                })
            
            # 检查重复运行的终端
            cmd_groups = defaultdict(list)
            for sid, session in self.sessions.items():
                if session.last_command:
                    key = f"{session.cwd}:{session.last_command}"
                    cmd_groups[key].append(sid)
            
            duplicate_sessions = []
            for key, sids in cmd_groups.items():
                if len(sids) > 1:
                    # 保留最新的，清除其他的
                    duplicate_sessions.extend(sids[:-1])
            
            if duplicate_sessions:
                suggestions.append({
                    "type": "kill_duplicate",
                    "message": f"建议清除 {len(duplicate_sessions)} 个重复终端",
                    "session_ids": duplicate_sessions
                })
        
        return {
            "memory": memory,
            "suggestions": suggestions,
            "should_cleanup": memory["percent"] >= self.memory_threshold
        }
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self.lock:
            running = sum(1 for s in self.sessions.values() if s.status == "running")
            idle = sum(1 for s in self.sessions.values() if s.status == "idle")
            completed = sum(1 for s in self.sessions.values() if s.status == "completed")
            
        memory = self.get_memory_usage()
        
        return {
            "total_sessions": len(self.sessions),
            "running": running,
            "idle": idle,
            "completed": completed,
            "memory_percent": memory["percent"],
            "memory_used_gb": round(memory["used"] / (1024**3), 2),
            "memory_total_gb": round(memory["total"] / (1024**3), 2)
        }
    
    def _start_smart_cleanup_thread(self):
        """启动智能清理线程（超过50个终端+内存不足时自动清理最老的已完成/空闲终端）"""
        import sys
        
        def smart_cleanup_worker():
            print("[SmartCleanup] 智能清理线程已启动", file=sys.stderr)
            print(f"[SmartCleanup] 策略: 超过{self.session_threshold}个终端时检查内存，内存不足或超过{self.max_sessions}个时清理", file=sys.stderr)
            print(f"[SmartCleanup] 空闲超时: {self.session_idle_timeout}秒", file=sys.stderr)
            sys.stderr.flush()
            
            while True:
                try:
                    time.sleep(5)  # 每5秒检查一次
                    
                    with self.lock:
                        session_count = len(self.sessions)
                    
                    # 检查是否超过最大限制
                    if session_count >= self.max_sessions:
                        print(f"[SmartCleanup] ⚠️ 终端数量达到上限({session_count}/{self.max_sessions})，强制清理", file=sys.stderr)
                        sys.stderr.flush()
                        self._force_cleanup_idle_sessions()
                        continue
                    
                    # 检查长时间空闲的终端
                    self._cleanup_timeout_sessions()
                    
                    # 只在超过阈值时才检查内存
                    if session_count <= self.session_threshold:
                        continue
                    
                    # 检查内存使用
                    memory = self.get_memory_usage()
                    memory_percent = memory["percent"]
                    
                    print(f"[SmartCleanup] 终端数: {session_count}, 内存使用: {memory_percent:.1f}%", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 内存充足，不清理
                    if memory_percent < self.memory_threshold:
                        print(f"[SmartCleanup] 内存充足({memory_percent:.1f}% < {self.memory_threshold}%)，不清理", file=sys.stderr)
                        sys.stderr.flush()
                        continue
                    
                    # 内存不足，需要清理
                    print(f"[SmartCleanup] ⚠️ 内存不足({memory_percent:.1f}% >= {self.memory_threshold}%)，开始清理", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 获取所有已完成/空闲的终端，按创建时间排序（最老的在前）
                    sessions_to_cleanup = []
                    
                    with self.lock:
                        for session_id, session in self.sessions.items():
                            # 只清理已完成或空闲且无运行命令的终端
                            if (session.status in ['completed', 'idle'] and 
                                session.current_command is None):
                                sessions_to_cleanup.append({
                                    'session_id': session_id,
                                    'created_at': session.created_at,
                                    'status': session.status,
                                    'age_seconds': (datetime.now() - session.created_at).total_seconds()
                                })
                    
                    if not sessions_to_cleanup:
                        print("[SmartCleanup] 没有可清理的终端（所有终端都在运行中）", file=sys.stderr)
                        sys.stderr.flush()
                        continue
                    
                    # 按创建时间排序，最老的在前
                    sessions_to_cleanup.sort(key=lambda x: x['created_at'])
                    
                    # 计算需要清理多少个（清理到内存降到阈值以下）
                    # 保守策略：每次清理10%的终端
                    cleanup_count = max(1, int(session_count * 0.1))
                    cleanup_count = min(cleanup_count, len(sessions_to_cleanup))
                    
                    print(f"[SmartCleanup] 找到 {len(sessions_to_cleanup)} 个可清理终端，计划清理 {cleanup_count} 个", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 清理最老的终端
                    for i in range(cleanup_count):
                        session_info = sessions_to_cleanup[i]
                        session_id = session_info['session_id']
                        age = session_info['age_seconds']
                        
                        print(f"[SmartCleanup] 清理终端: {session_id} (存在{age:.0f}秒, 状态:{session_info['status']})", file=sys.stderr)
                        sys.stderr.flush()
                        
                        try:
                            self.kill_session(session_id)
                        except Exception as e:
                            print(f"[SmartCleanup] 清理失败: {e}", file=sys.stderr)
                            sys.stderr.flush()
                    
                    # 清理后重新检查内存
                    memory_after = self.get_memory_usage()
                    print(f"[SmartCleanup] 清理完成，内存: {memory_after['percent']:.1f}%", file=sys.stderr)
                    sys.stderr.flush()
                
                except Exception as e:
                    print(f"[SmartCleanup] 异常: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
        
        cleanup_thread = threading.Thread(target=smart_cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_timeout_sessions(self):
        """清理超时的空闲终端"""
        import sys
        sessions_to_kill = []
        current_time = datetime.now()
        
        with self.lock:
            for session_id, session in self.sessions.items():
                # 检查空闲时间超时的终端
                if session.status == 'idle' and session.current_command is None:
                    # 计算空闲时间
                    if session.last_completed_at:
                        idle_seconds = (current_time - session.last_completed_at).total_seconds()
                    else:
                        idle_seconds = (current_time - session.created_at).total_seconds()
                    
                    # 超过空闲超时时间，加入清理列表
                    if idle_seconds > self.session_idle_timeout:
                        sessions_to_kill.append(session_id)
        
        # 清理超时的终端
        if sessions_to_kill:
            print(f"[SmartCleanup] 清理{len(sessions_to_kill)}个超时终端（空闲>{self.session_idle_timeout}s）", file=sys.stderr)
            sys.stderr.flush()
            self.kill_sessions(sessions_to_kill)
    
    def _force_cleanup_idle_sessions(self):
        """强制清理空闲和已完成的终端，直到数量低于上限"""
        import sys
        sessions_to_cleanup = []
        
        with self.lock:
            for session_id, session in self.sessions.items():
                # 收集所有空闲和已完成的终端
                if session.status in ['completed', 'idle'] and session.current_command is None:
                    sessions_to_cleanup.append({
                        'session_id': session_id,
                        'created_at': session.created_at,
                        'status': session.status
                    })
        
        # 按创建时间排序，最老的先清理
        sessions_to_cleanup.sort(key=lambda x: x['created_at'])
        
        # 计算需要清理的数量（保留至少20%的空间）
        current_count = len(self.sessions)
        target_count = int(self.max_sessions * 0.8)  # 清理到80%
        cleanup_count = min(len(sessions_to_cleanup), current_count - target_count)
        
        if cleanup_count > 0:
            sessions_to_kill = [s['session_id'] for s in sessions_to_cleanup[:cleanup_count]]
            print(f"[SmartCleanup] 强制清理{len(sessions_to_kill)}个终端（目标: {current_count} -> {target_count}）", file=sys.stderr)
            sys.stderr.flush()
            self.kill_sessions(sessions_to_kill)
    
    def cleanup_all_sessions(self):
        """清理所有终端（退出时调用）"""
        import sys
        print("[TerminalManager] 清理所有终端会话...", file=sys.stderr)
        sys.stderr.flush()
        
        session_ids = list(self.sessions.keys())
        if session_ids:
            self.kill_sessions(session_ids)
            print(f"[TerminalManager] 已清理{len(session_ids)}个终端", file=sys.stderr)
        else:
            print("[TerminalManager] 无终端需要清理", file=sys.stderr)
        sys.stderr.flush()
    
    # ==================== v2.0 new features ====================
    
    def detect_environment(self, session_id: str, force_refresh: bool = False) -> dict:
        """
        检测终端的环境信息（Node版本、Python版本、Git分支等）
        
        带全局超时保护，防止卡住
        
        Args:
            session_id: 会话ID
            force_refresh: 是否强制刷新（忽略缓存）
        
        Returns:
            环境信息字典
        """
        import sys
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # 检查缓存（5分钟内有效）
        if not force_refresh and session.environment_checked_at:
            age = (datetime.now() - session.environment_checked_at).total_seconds()
            if age < 300:  # 5分钟缓存
                return session.environment
        
        def _detect_with_timeout():
            """实际的检测逻辑，在独立线程中运行（极速模式：0.3秒超时）"""
            env_info = {}
            
            # Windows需要shell=True来解析PATH中的命令
            use_shell = (sys.platform == 'win32')
            
            # 检测Node.js版本（极速：0.5秒超时，增加时间以适应Windows）
            try:
                cmd = "node --version" if use_shell else ["node", "--version"]
                result = subprocess.run(
                    cmd,
                    cwd=session.cwd,
                    capture_output=True,
                    timeout=0.5,  # 增加到0.5秒以适应Windows
                    text=True,
                    shell=use_shell
                )
                if result.returncode == 0:
                    env_info["node_version"] = result.stdout.strip()
                else:
                    env_info["node_version"] = None
            except subprocess.TimeoutExpired:
                env_info["node_version"] = None  # 静默失败
            except Exception as e:
                print(f"[EnvDetect] Node检测异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                env_info["node_version"] = None  # 静默失败
            
            # 检测Python版本（极速：0.5秒超时）
            try:
                cmd = "python --version" if use_shell else ["python", "--version"]
                result = subprocess.run(
                    cmd,
                    cwd=session.cwd,
                    capture_output=True,
                    timeout=0.5,  # 增加到0.5秒
                    text=True,
                    shell=use_shell
                )
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    env_info["python_version"] = version
                else:
                    env_info["python_version"] = None
            except subprocess.TimeoutExpired:
                env_info["python_version"] = None  # 静默失败
            except Exception as e:
                print(f"[EnvDetect] Python检测异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                env_info["python_version"] = None  # 静默失败
            
            # 检测Git分支（极速：0.5秒超时）
            try:
                cmd = "git branch --show-current" if use_shell else ["git", "branch", "--show-current"]
                result = subprocess.run(
                    cmd,
                    cwd=session.cwd,
                    capture_output=True,
                    timeout=0.5,  # 增加到0.5秒
                    text=True,
                    shell=use_shell
                )
                if result.returncode == 0:
                    env_info["git_branch"] = result.stdout.strip()
                else:
                    env_info["git_branch"] = None
            except subprocess.TimeoutExpired:
                env_info["git_branch"] = None  # 静默失败
            except Exception as e:
                print(f"[EnvDetect] Git检测异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                env_info["git_branch"] = None  # 静默失败
            
            # 检测npm版本（极速：0.5秒超时）
            try:
                cmd = "npm --version" if use_shell else ["npm", "--version"]
                result = subprocess.run(
                    cmd,
                    cwd=session.cwd,
                    capture_output=True,
                    timeout=0.5,  # 增加到0.5秒
                    text=True,
                    shell=use_shell
                )
                if result.returncode == 0:
                    env_info["npm_version"] = result.stdout.strip()
                else:
                    env_info["npm_version"] = None
            except subprocess.TimeoutExpired:
                env_info["npm_version"] = None  # 静默失败
            except Exception as e:
                print(f"[EnvDetect] npm检测异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                env_info["npm_version"] = None  # 静默失败
            
            return env_info
        
        # 使用线程池+全局超时执行检测（适配Windows：2秒超时）
        executor = None
        try:
            print(f"[EnvDetect] 环境检测开始（全局2秒超时）: {session_id}", file=sys.stderr)
            sys.stderr.flush()
            
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(_detect_with_timeout)
            try:
                # 全局超时：2秒（适配Windows需要更多时间）
                env_info = future.result(timeout=2.0)
                print(f"[EnvDetect] ✅ 检测完成: {session_id}", file=sys.stderr)
                sys.stderr.flush()
            except FutureTimeoutError:
                print(f"[EnvDetect] ⏱️ 全局超时(2秒)，返回空结果: {session_id}", file=sys.stderr)
                sys.stderr.flush()
                # 取消future，不等待线程
                future.cancel()
                # 全局超时，返回所有null
                env_info = {
                    "node_version": None,
                    "python_version": None,
                    "git_branch": None,
                    "npm_version": None,
                    "timeout": True
                }
        except Exception as e:
            print(f"[ERROR] 环境检测异常 for {session_id}: {e}", file=sys.stderr)
            sys.stderr.flush()
            env_info = {
                "node_version": None,
                "python_version": None,
                "git_branch": None,
                "npm_version": None,
                "error": str(e)
            }
        finally:
            # 立即关闭线程池，不等待（使用wait=False）
            if executor:
                try:
                    # Python 3.9+ 支持 cancel_futures
                    import sys as _sys
                    if _sys.version_info >= (3, 9):
                        executor.shutdown(wait=False, cancel_futures=True)
                    else:
                        executor.shutdown(wait=False)
                    print(f"[DEBUG] 线程池已关闭(不等待): {session_id}", file=sys.stderr)
                    sys.stderr.flush()
                except Exception as ex:
                    print(f"[WARNING] 线程池关闭异常: {ex}", file=sys.stderr)
                    sys.stderr.flush()
        
        # 更新缓存
        session.environment = env_info
        session.environment_checked_at = datetime.now()
        
        return env_info
    
    def send_input(self, session_id: str, input_text: str, echo: bool = True) -> dict:
        """
        向终端发送输入（用于响应交互式命令）
        
        Args:
            session_id: 会话ID
            input_text: 要发送的输入文本
            echo: 是否回显输入
        
        Returns:
            操作结果
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        if not session.process or session.process.poll() is not None:
            return {
                "success": False,
                "error": "No active process"
            }
        
        try:
            # 发送输入到进程的stdin
            if session.process.stdin:
                # 确保使用正确的编码
                encoded_input = input_text.encode('utf-8')
                session.process.stdin.write(encoded_input)
                session.process.stdin.flush()
                
                # 更新状态
                session.waiting_input = False
                session.interaction_detected_at = None
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "input_sent": input_text if echo else "***",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Input sent successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Process stdin not available",
                    "suggestion": "Try using non-interactive command flags (e.g., -y, --non-interactive)",
                    "workaround": "Some commands may need to be run with non-interactive flags",
                    "session_id": session_id
                }
        except BrokenPipeError:
            return {
                "success": False,
                "error": "Broken pipe - process may have terminated",
                "suggestion": "Check if the process is still running",
                "session_id": session_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send input: {str(e)}",
                "error_type": type(e).__name__,
                "suggestion": "Try restarting the command or using non-interactive mode",
                "session_id": session_id
            }
    
    def detect_interactions(self, session_ids: Optional[List[str]] = None) -> dict:
        """
        检测所有等待输入的终端（非阻塞，立即返回）
        
        Args:
            session_ids: 要检查的会话ID列表，None表示检查所有
        
        Returns:
            交互检测结果
        """
        import sys
        print(f"[DetectInteractions] 开始检测交互状态", file=sys.stderr)
        sys.stderr.flush()
        
        if session_ids is None:
            with self.lock:
                session_ids = list(self.sessions.keys())
        
        print(f"[DetectInteractions] 检测 {len(session_ids)} 个会话", file=sys.stderr)
        sys.stderr.flush()
        
        interactions = []
        
        for idx, session_id in enumerate(session_ids):
            print(f"[DetectInteractions] [{idx+1}/{len(session_ids)}] 检查会话: {session_id}", file=sys.stderr)
            sys.stderr.flush()
            
            try:
                session = self.sessions.get(session_id)
                if not session:
                    print(f"[DetectInteractions] 会话 {session_id} 不存在", file=sys.stderr)
                    sys.stderr.flush()
                    continue
                
                print(f"[DetectInteractions] 检查会话 {session_id}, 进程存在:{session.process is not None}, 有命令:{session.current_command is not None}", file=sys.stderr)
                sys.stderr.flush()
                
                # 检查是否可能在等待输入（带超时保护）
                process_running = False
                if session.process:
                    try:
                        poll_result = session.process.poll()
                        process_running = (poll_result is None)
                        print(f"[DetectInteractions] 进程poll结果: {poll_result}, 运行中: {process_running}", file=sys.stderr)
                        sys.stderr.flush()
                    except Exception as e:
                        print(f"[DetectInteractions] poll异常: {e}", file=sys.stderr)
                        sys.stderr.flush()
                        process_running = False
                
                if process_running:
                    # 进程仍在运行，检查最近的输出
                    if session.current_output:
                        lines = session.current_output.strip().split('\n')
                        if lines:
                            last_line = lines[-1].strip()
                            
                            # 检测常见的输入提示模式
                            prompt_patterns = [
                            # 项目初始化
                            ("package name:", "text_input", "project_name"),
                            ("project name:", "text_input", "project_name"),
                            ("version:", "text_input", "version"),
                            ("description:", "text_input", "description"),
                            ("author:", "text_input", "author"),
                            
                            # 确认提示
                            ("(y/n)", "yes_no", None),
                            ("(Y/N)", "yes_no", None),
                            ("yes/no", "yes_no", None),
                            
                            # 选择提示
                            ("select", "choice", None),
                            ("choose", "choice", None),
                            
                                # 密码输入
                                ("password:", "password", None),
                                ("passphrase:", "password", None),
                            ]
                            
                            detected_pattern = None
                            prompt_type = "text_input"
                            pattern_name = None
                            
                            for pattern, ptype, pname in prompt_patterns:
                                if pattern.lower() in last_line.lower():
                                    detected_pattern = pattern
                                    prompt_type = ptype
                                    pattern_name = pname
                                    break
                            
                            # 如果检测到提示，或者输出长时间没有变化但进程还在运行
                            if detected_pattern or (
                                session.current_command_start_time and
                                (datetime.now() - session.current_command_start_time).total_seconds() > 3 and
                                session.last_output_length == len(session.current_output)
                            ):
                                # 检测到可能在等待输入
                                if not session.waiting_input:
                                    session.waiting_input = True
                                    session.interaction_detected_at = datetime.now()
                                    session.last_prompt_line = last_line
                                
                                waiting_seconds = (datetime.now() - session.interaction_detected_at).total_seconds()
                                
                                interaction = {
                                    "session_id": session_id,
                                    "command": session.current_command,
                                    "prompt": last_line,
                                    "waiting_seconds": round(waiting_seconds, 1),
                                    "last_output_line": last_line,
                                    "detected_pattern": detected_pattern or "unknown",
                                    "suggestions": {
                                        "type": prompt_type,
                                        "pattern_name": pattern_name
                                    }
                                }
                                
                                # 提取默认值
                                if "(" in last_line and ")" in last_line:
                                    start = last_line.find("(")
                                    end = last_line.find(")")
                                    default = last_line[start+1:end].strip()
                                    interaction["suggestions"]["default_value"] = default
                                
                                interactions.append(interaction)
            except Exception as e:
                print(f"[DetectInteractions] 处理会话 {session_id} 时异常: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                continue
        
        result = {
            "success": True,
            "interactions": interactions,
            "count": len(interactions)
        }
        
        print(f"[DetectInteractions] 完成，检测到 {len(interactions)} 个交互", file=sys.stderr)
        sys.stderr.flush()
        
        return result
    
    def get_terminal_states(self, session_ids: Optional[List[str]] = None, include_environment: bool = True) -> dict:
        """
        获取所有终端的详细状态（AI调度的核心工具）
        
        Args:
            session_ids: 要查询的会话ID列表，None表示所有
            include_environment: 是否包含环境信息（会增加一些延迟）
        
        Returns:
            终端状态字典
        """
        import sys
        print(f"[DEBUG] get_terminal_states开始执行", file=sys.stderr)
        sys.stderr.flush()
        
        try:
            if session_ids is None:
                print(f"[DEBUG] 获取所有会话列表", file=sys.stderr)
                sys.stderr.flush()
                session_ids = list(self.sessions.keys())
                print(f"[DEBUG] 找到 {len(session_ids)} 个会话", file=sys.stderr)
                sys.stderr.flush()
            
            terminals = {}
            summary = {
                "total": 0,
                "idle": 0,
                "running": 0,
                "waiting_input": 0,
                "completed": 0
            }
            
            for idx, session_id in enumerate(session_ids):
                print(f"[DEBUG] 处理会话 {idx+1}/{len(session_ids)}: {session_id}", file=sys.stderr)
                sys.stderr.flush()
                
                try:
                    session = self.sessions.get(session_id)
                    if not session:
                        print(f"[DEBUG] 会话 {session_id} 不存在，跳过", file=sys.stderr)
                        sys.stderr.flush()
                        continue
                    
                    print(f"[DEBUG] 检查会话状态: {session_id}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 确定状态
                    state = session.status
                    if session.waiting_input:
                        state = "waiting_input"
                    elif session.process:
                        try:
                            print(f"[DEBUG] 检查进程状态: {session_id}", file=sys.stderr)
                            sys.stderr.flush()
                            poll_result = session.process.poll()
                            if poll_result is None:
                                state = "running"
                            print(f"[DEBUG] 进程poll结果: {poll_result}", file=sys.stderr)
                            sys.stderr.flush()
                        except Exception as e:
                            print(f"[WARNING] poll失败 for {session_id}: {e}", file=sys.stderr)
                            sys.stderr.flush()
                    elif session.last_exit_code is not None:
                        state = "completed"
                    elif not session.last_command:
                        state = "idle"
                    
                    print(f"[DEBUG] 会话状态确定: {session_id} -> {state}", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 计算运行时间
                    running_seconds = 0
                    if session.current_command_start_time:
                        running_seconds = (datetime.now() - session.current_command_start_time).total_seconds()
                    
                    # 判断是否可以复用
                    can_reuse = (
                        state in ["idle", "completed"] and
                        session.current_command is None and
                        (not session.process or session.process.poll() is not None)
                    )
                    
                    terminal_state = {
                        "state": state,
                        "shell_type": session.shell_type,
                        "cwd": session.cwd,
                        "last_command": session.last_command,
                        "last_exit_code": session.last_exit_code,
                        "last_completed_at": session.last_completed_at.isoformat() if session.last_completed_at else None,
                        "current_command": session.current_command,
                        "running_seconds": round(running_seconds, 1),
                        "can_reuse": can_reuse,
                        "interaction_waiting": session.waiting_input,
                    }
                    
                    # 可选：包含环境信息
                    if include_environment:
                        print(f"[DEBUG] 开始检测环境: {session_id}", file=sys.stderr)
                        sys.stderr.flush()
                        try:
                            terminal_state["environment"] = self.detect_environment(session_id, force_refresh=False)
                            print(f"[DEBUG] 环境检测完成: {session_id}", file=sys.stderr)
                            sys.stderr.flush()
                        except Exception as e:
                            print(f"[WARNING] detect_environment失败 for {session_id}: {e}", file=sys.stderr)
                            sys.stderr.flush()
                            terminal_state["environment"] = {"error": str(e)}
                    else:
                        print(f"[DEBUG] 跳过环境检测: {session_id}", file=sys.stderr)
                        sys.stderr.flush()
                    
                    terminals[session_id] = terminal_state
                    
                    # 更新统计
                    summary["total"] += 1
                    if state == "idle":
                        summary["idle"] += 1
                    elif state == "running":
                        summary["running"] += 1
                    elif state == "waiting_input":
                        summary["waiting_input"] += 1
                    elif state == "completed":
                        summary["completed"] += 1
                    
                    print(f"[DEBUG] 会话处理完成: {session_id}", file=sys.stderr)
                    sys.stderr.flush()
                    
                except Exception as e:
                    print(f"[ERROR] 处理会话 {session_id} 时发生异常: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
                    # 继续处理下一个会话
                    continue
            
            print(f"[DEBUG] get_terminal_states完成，返回 {len(terminals)} 个终端状态", file=sys.stderr)
            sys.stderr.flush()
            
            return {
                "success": True,
                "terminals": terminals,
                "summary": summary
            }
        
        except Exception as e:
            print(f"[ERROR] get_terminal_states发生严重异常: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # 返回空结果而不是崩溃
            return {
                "success": False,
                "error": str(e),
                "terminals": {},
                "summary": {
                    "total": 0,
                    "idle": 0,
                    "running": 0,
                    "waiting_input": 0,
                    "completed": 0
                }
            }
    
    def wait_for_completion(
        self, 
        session_ids: List[str], 
        timeout: float = 300, 
        check_interval: float = 1.0
    ) -> dict:
        """
        等待一组终端完成（用于依赖管理）
        
        Args:
            session_ids: 要等待的会话ID列表
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            等待结果
        """
        import sys
        print(f"[WaitCompletion] 开始等待 {len(session_ids)} 个终端完成，超时{timeout}秒", file=sys.stderr)
        sys.stderr.flush()
        
        # 预检查：检测没有命令的会话
        no_command_sessions = []
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.current_command is None and session.last_command is None:
                no_command_sessions.append(session_id)
        
        if no_command_sessions:
            error_msg = f"⚠️ 以下会话没有执行任何命令，无法等待完成：{', '.join(no_command_sessions)}"
            print(f"[WaitCompletion] {error_msg}", file=sys.stderr)
            sys.stderr.flush()
            return {
                "success": False,
                "error": error_msg,
                "no_command_sessions": no_command_sessions,
                "suggestion": "请先使用 execute_command 执行命令，或使用 create_session(initial_command='...') 创建时直接执行命令",
                "completed": [],
                "failed": [],
                "timeout": [],
                "still_running": [],
                "results": {},
                "elapsed_time": 0
            }
        
        start_time = time.time()
        completed = []
        failed = []
        timeout_sessions = []
        
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                # 记录超时的会话
                for sid in session_ids:
                    if sid not in completed and sid not in failed:
                        timeout_sessions.append(sid)
                print(f"[WaitCompletion] 超时！{len(timeout_sessions)}个会话超时", file=sys.stderr)
                sys.stderr.flush()
                break
            
            # 检查每个会话
            all_done = True
            for session_id in session_ids:
                if session_id in completed or session_id in failed:
                    continue
                
                session = self.sessions.get(session_id)
                if not session:
                    print(f"[WaitCompletion] 会话 {session_id} 不存在", file=sys.stderr)
                    sys.stderr.flush()
                    failed.append(session_id)
                    continue
                
                # 检查进程状态
                if session.process:
                    returncode = session.process.poll()
                    if returncode is not None:
                        # 进程已结束
                        if returncode == 0:
                            print(f"[WaitCompletion] 会话 {session_id} 成功完成", file=sys.stderr)
                            sys.stderr.flush()
                            completed.append(session_id)
                        else:
                            print(f"[WaitCompletion] 会话 {session_id} 失败 (exit={returncode})", file=sys.stderr)
                            sys.stderr.flush()
                            failed.append(session_id)
                    else:
                        # 进程仍在运行
                        print(f"[WaitCompletion] 会话 {session_id} 仍在运行... ({elapsed:.1f}s)", file=sys.stderr)
                        sys.stderr.flush()
                        all_done = False
                else:
                    # 没有活动进程
                    print(f"[WaitCompletion] 会话 {session_id} 没有进程，检查状态", file=sys.stderr)
                    sys.stderr.flush()
                    
                    # 如果有退出码，说明已经执行过命令
                    if session.last_exit_code is not None:
                        if session.last_exit_code == 0:
                            completed.append(session_id)
                        else:
                            failed.append(session_id)
                    # 如果从未执行过命令（这个不应该发生，因为预检查已经过滤了）
                    elif session.current_command is None and session.last_command is None:
                        print(f"[WaitCompletion] ⚠️ 会话 {session_id} 从未执行命令（预检查遗漏），标记为失败", file=sys.stderr)
                        sys.stderr.flush()
                        failed.append(session_id)
                    else:
                        # 有命令但无进程，可能已完成
                        completed.append(session_id)
            
            if all_done:
                break
            
            # 等待下一次检查
            time.sleep(check_interval)
        
        # 收集结果详情
        results = {}
        for session_id in completed + failed:
            session = self.sessions.get(session_id)
            if session:
                duration = 0
                if session.current_command_start_time and session.last_completed_at:
                    duration = (session.last_completed_at - session.current_command_start_time).total_seconds()
                
                results[session_id] = {
                    "exit_code": session.last_exit_code,
                    "duration": round(duration, 1)
                }
        
        # 仍在运行的会话
        still_running = [sid for sid in session_ids if sid not in completed and sid not in failed and sid not in timeout_sessions]
        
        result = {
            "success": True,
            "completed": completed,
            "failed": failed,
            "timeout": timeout_sessions,
            "still_running": still_running,
            "results": results,
            "elapsed_time": round(time.time() - start_time, 1)
        }
        
        print(f"[WaitCompletion] 完成: 成功{len(completed)}, 失败{len(failed)}, 超时{len(timeout_sessions)}, 仍运行{len(still_running)}", file=sys.stderr)
        sys.stderr.flush()
        
        return result
    
    def send_keys(self, session_id: str, keys: str, is_text: bool = False) -> dict:
        """
        发送按键或文本到终端（v1.0.2新增）
        
        Args:
            session_id: 会话ID
            keys: 按键名称或文本内容
                  - 按键名称: "UP", "CTRL_C", "F1", "Ctrl+C" 等
                  - 文本内容: 任意字符串（当is_text=True时）
            is_text: 是否作为普通文本发送（True）还是解析为按键（False）
        
        Returns:
            操作结果
        """
        # 修复导入错误：使用绝对导入而不是相对导入
        try:
            from src.key_mapper import KeyMapper
        except ImportError:
            # 如果src.key_mapper导入失败，尝试直接导入
            try:
                import key_mapper
                KeyMapper = key_mapper.KeyMapper
            except ImportError:
                # 最后尝试相对导入
                from .key_mapper import KeyMapper
        
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        session = self.sessions[session_id]
        
        with session.lock:
            if not session.process or session.process.poll() is not None:
                return {
                    "success": False,
                    "error": "No running process",
                    "session_id": session_id,
                    "message": "终端当前没有运行进程"
                }
            
            try:
                # 转换按键为控制序列
                if is_text:
                    # 作为普通文本发送
                    input_data = KeyMapper.map_text(keys)
                else:
                    # 解析为按键
                    input_data = KeyMapper.map_key(keys)
                
                # 发送到进程的stdin
                if session.process.stdin:
                    try:
                        session.process.stdin.write(input_data.encode('utf-8'))
                        session.process.stdin.flush()
                        
                        return {
                            "success": True,
                            "session_id": session_id,
                            "sent": keys,
                            "is_text": is_text,
                            "message": f"Successfully sent: {keys}"
                        }
                    except BrokenPipeError:
                        return {
                            "success": False,
                            "error": "Broken pipe - process may have terminated",
                            "session_id": session_id,
                            "suggestion": "Check if process is still running"
                        }
                else:
                    return {
                        "success": False,
                        "error": "Process stdin not available",
                        "session_id": session_id,
                        "suggestion": "Terminal may not support input in current mode"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to send keys: {str(e)}",
                    "error_type": type(e).__name__,
                    "session_id": session_id,
                    "suggestion": "Try using send_text for simple text input"
                }
    
    def send_text(self, session_id: str, text: str) -> dict:
        """
        快速发送文本到终端（v1.0.2新增）
        这是send_keys的便捷方法，专门用于发送文本
        
        Args:
            session_id: 会话ID
            text: 要发送的文本
        
        Returns:
            操作结果
        """
        return self.send_keys(session_id, text, is_text=True)
    
    def get_live_output(self, session_id: str, since: Optional[str] = None, max_lines: int = 100) -> dict:
        """
        获取实时输出流（v1.0.2新增）
        
        Args:
            session_id: 会话ID
            since: 从某个时间点开始获取（ISO格式），None表示获取最新的
            max_lines: 最大返回行数
        
        Returns:
            实时输出内容
        """
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        session = self.sessions[session_id]
        
        with session.lock:
            # 追踪查询次数（防止AI循环调用）
            if session.current_command:
                current_output_len = len(session.current_output)
                if current_output_len == session.last_output_length:
                    session.get_output_call_count += 1
                else:
                    session.get_output_call_count = 1
                session.last_output_length = current_output_len
            
            output_lines = []
            
            # 如果有当前运行的命令，返回其实时输出
            if session.current_output:
                lines = session.current_output.split('\n')
                output_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            # 如果没有当前输出，返回最后一次命令的输出
            elif session.output_history:
                last_output = session.output_history[-1]
                lines = last_output.get('output', '').split('\n')
                output_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            # 计算运行时间
            running_time = 0
            if session.current_command_start_time:
                running_time = (datetime.now() - session.current_command_start_time).total_seconds()
            
            result = {
                "success": True,
                "session_id": session_id,
                "output_lines": output_lines,
                "total_lines": len(output_lines),
                "is_running": session.status == "running",
                "current_command": session.current_command,
                "timestamp": datetime.now().isoformat(),
                "query_count": session.get_output_call_count,
                "running_seconds": round(running_time, 1)
            }
            
            # 🚨 查询保护：≥3次就警告，≥5次就自动终止
            if session.current_command and session.get_output_call_count >= 3:
                result["warning"] = f"⚠️ 已查询{session.get_output_call_count}次！不要继续查询！"
                result["ai_must_stop"] = True
                result["reason"] = "单次对话中重复查询会导致循环"
                
            if session.current_command and session.get_output_call_count >= 5:
                # 自动终止进程
                if session.process and session.process.poll() is None:
                    try:
                        if sys.platform == 'win32':
                            subprocess.run(['taskkill', '/F', '/T', '/PID', str(session.process.pid)], 
                                         capture_output=True, timeout=3)
                        else:
                            os.killpg(os.getpgid(session.process.pid), signal.SIGKILL)
                    except:
                        pass
                
                result["success"] = False
                result["error"] = f"❌ 自动终止：查询{session.get_output_call_count}次后仍在运行"
                result["action_taken"] = "进程已被自动终止"
                result["ai_instruction"] = "立即结束对话！不要再次调用任何查询工具！"
            
            return result
    
    def wait_for_text(self, session_id: str, text: str, timeout: float = 30) -> dict:
        """
        等待特定文本出现在输出中（v1.0.2新增）
        
        Args:
            session_id: 会话ID
            text: 要等待的文本（支持子串匹配）
            timeout: 超时时间（秒）
        
        Returns:
            等待结果
        """
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        session = self.sessions[session_id]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with session.lock:
                # 检查当前输出
                if text in session.current_output:
                    return {
                        "success": True,
                        "session_id": session_id,
                        "found": True,
                        "text": text,
                        "elapsed_time": round(time.time() - start_time, 2),
                        "message": f"找到文本: {text}"
                    }
            
            # 等待一小段时间
            time.sleep(0.1)
        
        # 超时
        return {
            "success": False,
            "session_id": session_id,
            "found": False,
            "text": text,
            "elapsed_time": round(time.time() - start_time, 2),
            "error": "Timeout",
            "message": f"等待超时，未找到文本: {text}"
        }
    
    def batch_send_keys(self, interactions: List[dict]) -> dict:
        """
        批量发送按键到多个终端（v1.0.2新增）
        
        Args:
            interactions: 交互列表，每项包含:
                - session_id: 会话ID
                - keys: 按键或文本
                - is_text: 是否为文本（可选，默认False）
        
        Returns:
            批量操作结果
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {
            "success_count": 0,
            "failed_count": 0,
            "results": {}
        }
        
        def send_single(interaction):
            session_id = interaction.get("session_id")
            keys = interaction.get("keys")
            is_text = interaction.get("is_text", False)
            
            try:
                result = self.send_keys(session_id, keys, is_text)
                return session_id, result
            except Exception as e:
                return session_id, {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id
                }
        
        # 并发发送（最多100线程，提升发送性能）
        max_workers = min(100, max(10, len(interactions)))
        
        print(f"[BatchSendKeys] 使用 {max_workers} 个线程并发发送", file=sys.stderr)
        sys.stderr.flush()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(send_single, interaction): interaction for interaction in interactions}
            
            for future in as_completed(futures):
                try:
                    session_id, result = future.result()
                    if result.get("success"):
                        results["success_count"] += 1
                    else:
                        results["failed_count"] += 1
                    results["results"][session_id] = result
                except Exception as e:
                    results["failed_count"] += 1
        
        results["total"] = len(interactions)
        results["message"] = f"批量发送完成: 成功{results['success_count']}/{results['total']}"
        
        return results
    
    # ==================== v1.0.51 新功能 ====================
    
    def wait_until_complete(
        self, 
        session_ids: List[str], 
        timeout: int = 300,
        poll_interval: float = 1.0,
        verbose: bool = True
    ) -> dict:
        """
        智能等待终端完成（阻塞式）
        
        Args:
            session_ids: 要等待的会话ID列表
            timeout: 超时时间（秒），默认300秒
            poll_interval: 轮询间隔（秒），默认1秒
            verbose: 是否打印详细信息
        
        Returns:
            {
                "success": bool,
                "completed": List[str],  # 已完成的会话
                "timeout": List[str],    # 超时的会话
                "failed": List[str],     # 失败的会话
                "results": dict          # 每个会话的结果
            }
        """
        import sys
        if verbose:
            print(f"[WaitComplete] 开始等待 {len(session_ids)} 个终端完成...", file=sys.stderr)
            sys.stderr.flush()
        
        start_time = time.time()
        completed = []
        timeout_sessions = []
        failed_sessions = []
        results = {}
        
        # 等待所有会话完成或超时
        while session_ids:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                # 超时，剩余的都算超时
                timeout_sessions.extend(session_ids)
                for sid in session_ids:
                    results[sid] = {
                        "status": "timeout",
                        "elapsed_time": round(elapsed, 2)
                    }
                break
            
            # 检查每个会话
            for sid in list(session_ids):
                session = self.sessions.get(sid)
                if not session:
                    failed_sessions.append(sid)
                    results[sid] = {"status": "not_found"}
                    session_ids.remove(sid)
                    continue
                
                # 检查是否完成
                is_running = session.process and session.process.poll() is None
                
                if not is_running:
                    # 完成了
                    exit_code = session.process.returncode if session.process else None
                    completed.append(sid)
                    results[sid] = {
                        "status": "completed",
                        "exit_code": exit_code,
                        "elapsed_time": round(time.time() - start_time, 2),
                        "command": session.current_command or session.last_command
                    }
                    session_ids.remove(sid)
                    
                    if verbose:
                        status_icon = "✅" if exit_code == 0 else "❌"
                        print(f"[WaitComplete] {status_icon} {sid} 完成 (退出码: {exit_code})", file=sys.stderr)
                        sys.stderr.flush()
            
            # 等待下一轮
            if session_ids:
                time.sleep(poll_interval)
        
        total_elapsed = time.time() - start_time
        
        return {
            "success": len(failed_sessions) == 0 and len(timeout_sessions) == 0,
            "completed": completed,
            "timeout": timeout_sessions,
            "failed": failed_sessions,
            "results": results,
            "total_elapsed_time": round(total_elapsed, 2),
            "message": f"等待完成: ✅{len(completed)} ⏱{len(timeout_sessions)} ❌{len(failed_sessions)}"
        }
    
    async def execute_sequence(
        self,
        commands: List[Tuple[str, str]],
        stop_on_error: bool = True,
        timeout_per_command: int = 300
    ) -> dict:
        """
        顺序执行命令（一个接一个）
        
        Args:
            commands: 命令列表 [(session_id, command), ...]
            stop_on_error: 遇到错误是否停止，默认True
            timeout_per_command: 每个命令的超时时间（秒）
        
        Returns:
            {
                "success": bool,
                "executed": List[dict],  # 已执行的命令结果
                "skipped": List[dict],   # 跳过的命令
                "total_time": float
            }
        """
        import sys
        print(f"[ExecuteSequence] 开始顺序执行 {len(commands)} 个命令", file=sys.stderr)
        sys.stderr.flush()
        
        start_time = time.time()
        executed = []
        skipped = []
        
        for idx, (session_id, command) in enumerate(commands, 1):
            print(f"[ExecuteSequence] [{idx}/{len(commands)}] 执行: {session_id} - {command[:50]}...", file=sys.stderr)
            sys.stderr.flush()
            
            # 执行命令（异步方式）
            exec_result = await self.execute_command(session_id, command)
            
            # 检查命令是否成功启动（status应该是"started"而不是"error"）
            if exec_result.get("status") == "error":
                result = {
                    "session_id": session_id,
                    "command": command,
                    "status": "failed_to_start",
                    "error": exec_result.get("error")
                }
                executed.append(result)
                
                if stop_on_error:
                    # 跳过剩余命令
                    for remaining_sid, remaining_cmd in commands[idx:]:
                        skipped.append({
                            "session_id": remaining_sid,
                            "command": remaining_cmd,
                            "reason": "previous_command_failed"
                        })
                    break
                continue
            
            # 等待命令完成
            wait_result = self.wait_until_complete([session_id], timeout=timeout_per_command, verbose=False)
            
            cmd_result = wait_result["results"].get(session_id, {})
            result = {
                "session_id": session_id,
                "command": command,
                "status": cmd_result.get("status"),
                "exit_code": cmd_result.get("exit_code"),
                "elapsed_time": cmd_result.get("elapsed_time")
            }
            executed.append(result)
            
            # 检查是否失败 (exit_code为None或0都算成功)
            exit_code = cmd_result.get("exit_code")
            if exit_code is not None and exit_code != 0 and stop_on_error:
                print(f"[ExecuteSequence] ❌ 命令失败 (退出码: {exit_code}), 停止执行", file=sys.stderr)
                sys.stderr.flush()
                
                # 跳过剩余命令
                for remaining_sid, remaining_cmd in commands[idx:]:
                    skipped.append({
                        "session_id": remaining_sid,
                        "command": remaining_cmd,
                        "reason": "previous_command_failed"
                    })
                break
            
            print(f"[ExecuteSequence] ✅ 命令完成", file=sys.stderr)
            sys.stderr.flush()
        
        total_time = time.time() - start_time
        # 成功条件：所有命令的exit_code都是None或0
        success = all(r.get("exit_code") in [None, 0] for r in executed if "exit_code" in r)
        
        return {
            "success": success,
            "executed": executed,
            "skipped": skipped,
            "total_time": round(total_time, 2),
            "message": f"顺序执行完成: ✅{len([r for r in executed if r.get('exit_code') in [None, 0]])} ❌{len([r for r in executed if r.get('exit_code') not in [None, 0]])} ⏭{len(skipped)}"
        }
    
    async def execute_with_retry(
        self,
        session_id: str,
        command: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_on_exit_codes: List[int] = None,
        timeout_per_try: int = 300
    ) -> dict:
        """
        执行命令并自动重试
        
        Args:
            session_id: 会话ID
            command: 要执行的命令
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试延迟（秒），默认1秒
            retry_on_exit_codes: 哪些退出码需要重试，None表示所有非0退出码
            timeout_per_try: 每次尝试的超时时间（秒）
        
        Returns:
            {
                "success": bool,
                "attempts": int,  # 尝试次数
                "final_exit_code": int,
                "retry_history": List[dict]
            }
        """
        import sys
        print(f"[ExecuteWithRetry] 执行命令 (最多{max_retries+1}次): {command[:50]}...", file=sys.stderr)
        sys.stderr.flush()
        
        retry_history = []
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"[ExecuteWithRetry] 重试 {attempt}/{max_retries}...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(retry_delay)
            
            # 执行命令（异步方式）
            exec_result = await self.execute_command(session_id, command)
            
            # 检查命令是否成功启动（status应该是"started"而不是"error"）
            if exec_result.get("status") == "error":
                retry_history.append({
                    "attempt": attempt + 1,
                    "status": "failed_to_start",
                    "error": exec_result.get("error")
                })
                continue
            
            # 等待完成
            wait_result = self.wait_until_complete([session_id], timeout=timeout_per_try, verbose=False)
            cmd_result = wait_result["results"].get(session_id, {})
            
            exit_code = cmd_result.get("exit_code")
            retry_history.append({
                "attempt": attempt + 1,
                "exit_code": exit_code,
                "elapsed_time": cmd_result.get("elapsed_time"),
                "status": cmd_result.get("status")
            })
            
            # 检查是否成功 (exit_code为None或0都算成功)
            if exit_code is None or exit_code == 0:
                print(f"[ExecuteWithRetry] ✅ 命令成功 (尝试次数: {attempt+1})", file=sys.stderr)
                sys.stderr.flush()
                return {
                    "success": True,
                    "attempts": attempt + 1,
                    "final_exit_code": exit_code,
                    "retry_history": retry_history,
                    "message": f"命令成功 (尝试{attempt+1}次)"
                }
            
            # 检查是否需要重试
            if retry_on_exit_codes is not None and exit_code not in retry_on_exit_codes:
                # 不需要重试这个退出码
                print(f"[ExecuteWithRetry] ❌ 命令失败 (退出码: {exit_code}, 不重试)", file=sys.stderr)
                sys.stderr.flush()
                break
        
        # 所有重试都失败了
        final_exit_code = retry_history[-1].get("exit_code") if retry_history else None
        print(f"[ExecuteWithRetry] ❌ 命令最终失败 (尝试{len(retry_history)}次)", file=sys.stderr)
        sys.stderr.flush()
        
        return {
            "success": False,
            "attempts": len(retry_history),
            "final_exit_code": final_exit_code,
            "retry_history": retry_history,
            "message": f"命令失败 (尝试{len(retry_history)}次)"
        }
    
    async def execute_workflow(
        self,
        tasks: List[dict],
        timeout: int = 600
    ) -> dict:
        """
        执行工作流（支持依赖关系）
        
        Args:
            tasks: 任务列表，每个任务包含:
                - name: 任务名称（唯一标识）
                - session_id: 会话ID
                - command: 要执行的命令
                - depends_on: 依赖的任务名称列表（可选）
                - retry: 是否重试（可选，默认False）
                - max_retries: 最大重试次数（可选，默认3）
            timeout: 总超时时间（秒）
        
        Returns:
            {
                "success": bool,
                "completed": List[str],  # 已完成的任务
                "failed": List[str],     # 失败的任务
                "skipped": List[str],    # 跳过的任务
                "results": dict          # 每个任务的结果
            }
        """
        import sys
        from concurrent.futures import ThreadPoolExecutor, as_completed, Future
        
        print(f"[Workflow] 开始执行工作流: {len(tasks)} 个任务", file=sys.stderr)
        sys.stderr.flush()
        
        start_time = time.time()
        
        # 构建任务依赖图
        task_map = {task["name"]: task for task in tasks}
        completed_tasks = set()
        failed_tasks = set()
        skipped_tasks = set()
        results = {}
        
        # 验证依赖关系
        for task in tasks:
            for dep in task.get("depends_on", []):
                if dep not in task_map:
                    print(f"[Workflow] ❌ 任务 '{task['name']}' 依赖不存在的任务 '{dep}'", file=sys.stderr)
                    sys.stderr.flush()
                    return {
                        "success": False,
                        "error": f"依赖关系错误: '{task['name']}' depends on '{dep}' which doesn't exist"
                    }
        
        # 拓扑排序 - 找出可以并行执行的任务组
        def get_ready_tasks():
            """获取所有依赖已满足的任务"""
            ready = []
            for task_name, task in task_map.items():
                if task_name in completed_tasks or task_name in failed_tasks or task_name in skipped_tasks:
                    continue
                
                deps = task.get("depends_on", [])
                # 检查所有依赖是否都已完成
                if all(dep in completed_tasks for dep in deps):
                    # 检查是否有失败的依赖
                    if any(dep in failed_tasks for dep in deps):
                        skipped_tasks.add(task_name)
                        results[task_name] = {
                            "status": "skipped",
                            "reason": "dependency_failed"
                        }
                        print(f"[Workflow] ⏭ 跳过任务 '{task_name}' (依赖失败)", file=sys.stderr)
                        sys.stderr.flush()
                        continue
                    
                    ready.append(task)
            return ready
        
        # 执行单个任务（异步）
        async def execute_task(task):
            task_name = task["name"]
            session_id = task["session_id"]
            command = task["command"]
            use_retry = task.get("retry", False)
            max_retries = task.get("max_retries", 3)
            
            print(f"[Workflow] 🚀 开始任务 '{task_name}': {command[:50]}...", file=sys.stderr)
            sys.stderr.flush()
            
            try:
                if use_retry:
                    result = await self.execute_with_retry(
                        session_id, 
                        command,
                        max_retries=max_retries
                    )
                else:
                    # 执行命令（异步方式）
                    exec_result = await self.execute_command(session_id, command)
                    
                    # 检查命令是否成功启动（status应该是"started"而不是"error"）
                    if exec_result.get("status") == "error":
                        return task_name, {
                            "status": "failed",
                            "error": exec_result.get("error")
                        }
                    
                    # 等待完成
                    wait_result = self.wait_until_complete([session_id], timeout=300, verbose=False)
                    cmd_result = wait_result["results"].get(session_id, {})
                    
                    result = {
                        "exit_code": cmd_result.get("exit_code"),
                        "elapsed_time": cmd_result.get("elapsed_time"),
                        "status": cmd_result.get("status")
                    }
                
                return task_name, result
            
            except Exception as e:
                print(f"[Workflow] ❌ 任务 '{task_name}' 异常: {e}", file=sys.stderr)
                sys.stderr.flush()
                return task_name, {
                    "status": "exception",
                    "error": str(e)
                }
        
        # 主循环：持续执行直到所有任务完成或超时
        import asyncio
        running_tasks = {}  # Task -> task_name
        
        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                print(f"[Workflow] ⏱ 工作流超时", file=sys.stderr)
                sys.stderr.flush()
                # 标记所有未完成的任务为超时
                for task_name in task_map:
                    if task_name not in completed_tasks and task_name not in failed_tasks and task_name not in skipped_tasks:
                        results[task_name] = {"status": "timeout"}
                        failed_tasks.add(task_name)
                break
            
            # 获取可执行的任务
            ready_tasks = get_ready_tasks()
            
            # 启动新任务
            for task in ready_tasks:
                async_task = asyncio.create_task(execute_task(task))
                running_tasks[async_task] = task["name"]
            
            # 如果没有正在运行的任务，退出
            if not running_tasks:
                break
            
            # 等待至少一个任务完成
            done, pending = await asyncio.wait(running_tasks.keys(), timeout=1.0, return_when=asyncio.FIRST_COMPLETED)
            
            for async_task in done:
                task_name = running_tasks.pop(async_task)
                try:
                    _, result = await async_task
                    results[task_name] = result
                    
                    # 判断任务是否成功（支持两种返回格式）
                    # 1. retry任务：{"success": true, ...}
                    # 2. 普通任务：{"status": "completed", "exit_code": null/0}
                    is_success = False
                    
                    if "success" in result:
                        # retry任务的返回格式
                        is_success = result.get("success") == True
                    else:
                        # 普通任务的返回格式
                        exit_code = result.get("exit_code") or result.get("final_exit_code")
                        is_success = result.get("status") in ["completed", "success"] and (exit_code is None or exit_code == 0)
                    
                    if is_success:
                        completed_tasks.add(task_name)
                        print(f"[Workflow] ✅ 任务 '{task_name}' 完成", file=sys.stderr)
                        sys.stderr.flush()
                    else:
                        failed_tasks.add(task_name)
                        print(f"[Workflow] ❌ 任务 '{task_name}' 失败", file=sys.stderr)
                        sys.stderr.flush()
                
                except Exception as e:
                    failed_tasks.add(task_name)
                    results[task_name] = {
                        "status": "exception",
                        "error": str(e)
                    }
                    print(f"[Workflow] ❌ 任务 '{task_name}' 异常: {e}", file=sys.stderr)
                    sys.stderr.flush()
        
        total_time = time.time() - start_time
        success = len(failed_tasks) == 0 and len(completed_tasks) == len(tasks)
        
        print(f"[Workflow] 工作流完成: ✅{len(completed_tasks)} ❌{len(failed_tasks)} ⏭{len(skipped_tasks)}", file=sys.stderr)
        sys.stderr.flush()
        
        return {
            "success": success,
            "completed": list(completed_tasks),
            "failed": list(failed_tasks),
            "skipped": list(skipped_tasks),
            "results": results,
            "total_time": round(total_time, 2),
            "message": f"工作流完成: ✅{len(completed_tasks)} ❌{len(failed_tasks)} ⏭{len(skipped_tasks)} (耗时{round(total_time, 2)}秒)"
        }

