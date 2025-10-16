# AI-MCP Terminal

[![PyPI](https://badge.fury.io/py/ai-mcp-terminal.svg)](https://pypi.org/project/ai-mcp-terminal/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 Multi-threaded terminal management for AI assistants with real-time web monitoring

**Solve terminal blocking issues** - Commands run async, never block AI operations. Monitor up to **100 concurrent terminals** with intelligent cleanup and system tracking.

---

## ✨ Key Features

* 🚀 **Async Execution** - Commands never block AI operations
* 🔢 **Multi-Threading** - 100 concurrent terminals with ThreadPoolExecutor
* 🧹 **Auto Cleanup** - Smart idle session detection & memory management
* ⚡ **Batch Operations** - Execute across multiple terminals simultaneously
* 📊 **Web Monitor** - Real-time xterm.js interface with system stats
* 🐧 **Smart Shell** - Auto-detect best shell (bash > PowerShell > cmd)
* 🌐 **UTF-8 Support** - Proper encoding, no garbled text
* 🛑 **Anti-Loop Protection** - Prevents AI from getting stuck in query loops

---

## 🚀 Quick Start (1 Minute)

### Step 1: Add MCP Configuration

Add to your Cursor/Cline MCP settings:

```json
{
  "mcpServers": {
    "ai-mcp-terminal": {
      "command": "uvx",
      "args": ["ai-mcp-terminal"],
      "env": {}
    }
  }
}
```

### Step 2: Restart IDE

### Step 3: Start Using

In Cursor:

```
Create 3 terminals and run system checks in parallel
```

**AI will use `create_batch` for true concurrency!**

Browser auto-opens → `http://localhost:8000` → View all terminals in real-time!

---

## 📊 Web Interface

Auto-opens at `http://localhost:8000`

**Features**:
- 📺 Real-time xterm.js terminals
- 📊 CPU/Memory/System stats  
- 🔄 Live output streaming
- 🎯 Click to expand terminals
- 🛑 Shutdown server button

---

## 🛠️ Available MCP Tools

### Core Tools

| Tool | Description | Concurrency |
|------|-------------|-------------|
| `create_batch` | Create multiple terminals + execute | ✅ 100 threads |
| `execute_batch` | Execute across terminals | ✅ 100 threads |
| `get_batch_output` | Get all outputs | ✅ 100 threads |
| `check_completion` | Check status | ✅ 100 threads |
| `broadcast_command` | Send to all terminals | ✅ Async |

### Single Tools (Use batch tools instead!)

| Tool | Use Instead |
|------|-------------|
| `create_session` | → `create_batch` |
| `execute_command` | → `execute_batch` |
| `get_output` | → `get_batch_output` |

**Why batch tools?**
- 10x faster (parallel execution)
- 1 call instead of 10 calls
- Non-blocking design

---

## 🎯 Use Cases

### Multi-Service Development

```
User: "Start frontend, backend, and database"

AI calls:
create_batch(sessions=[
  {name: "frontend", cwd: "./web", initial_command: "npm run dev"},
  {name: "backend", cwd: "./api", initial_command: "python app.py"},
  {name: "db", cwd: "./", initial_command: "docker-compose up"}
])

Result: 3 services start simultaneously, web interface shows all
```

### System Information Gathering

```
User: "Check system info"

AI calls:
create_batch(sessions=[
  {name: "cpu", cwd: ".", initial_command: "wmic cpu get name"},
  {name: "mem", cwd: ".", initial_command: "wmic memorychip get capacity"},
  {name: "disk", cwd: ".", initial_command: "wmic logicaldisk get size,freespace"},
  {name: "os", cwd: ".", initial_command: "systeminfo"}
])

Later:
get_batch_output(session_ids=["cpu", "mem", "disk", "os"])

Result: All info gathered in parallel, 4x faster than serial
```

---

## ⚙️ Configuration

Optional environment variables:

```json
{
  "mcpServers": {
    "ai-mcp-terminal": {
      "command": "uvx",
      "args": ["ai-mcp-terminal"],
      "env": {
        "AI_MCP_PREFERRED_SHELL": "bash"
      }
    }
  }
}
```

**Shell Priority**:
- Windows: `WSL bash` → `Git Bash` → `powershell` → `cmd`
- macOS: `zsh` → `bash` → `sh`
- Linux: `bash` → `zsh` → `sh`

---

## 🔧 Installation Options

### Option 1: UVX (Recommended)

    ```json
    {
  "command": "uvx",
  "args": ["ai-mcp-terminal"]
}
```

**No installation needed!** UV handles everything.

### Option 2: PIPX

```bash
pipx install ai-mcp-terminal
```

    ```json
    {
  "command": "ai-mcp-terminal"
}
```

### Option 3: PIP

```bash
pip install ai-mcp-terminal
```

```json
{
      "command": "python",
  "args": ["-m", "src.main"]
}
```

---

## 🛡️ Anti-Loop Protection

**Problem**: AI gets stuck querying terminal repeatedly

**Solution**: Built-in query counter

- Query 1-2: Normal
- Query 3-4: ⚠️ Warning + stop instruction  
- Query ≥5: 🔪 Auto-terminate process

**Result**: AI never loops, always proceeds with tasks

---

## 🚦 How AI Should Use This

### ✅ Correct Pattern

```
Dialog 1:
User: "Deploy React app"
AI: 
  1. create_batch(...) 
  2. Reply: "Deploying in background..."
  3. END conversation

Dialog 2 (later):
User: "Is it done?"
AI:
  1. check_completion(...)
  2. Reply: "Still running..." or "Done!"
  3. END conversation
```

### ❌ Wrong Pattern (Fixed by protection)

```
Dialog 1:
User: "Deploy React app"
AI:
  1. execute_command(...)
  2. get_output(...) → running
  3. get_output(...) → running  [Query 2]
  4. get_output(...) → running  [Query 3 - WARNING]
  5. get_output(...) → running  [Query 4]
  6. get_output(...) → AUTO-KILLED [Query 5]
  7. Error: "Loop detected, process terminated"
```

---

## 📁 Project Structure

```
ai-mcp-terminal/
├── src/
│   ├── main.py              # Entry point
│   ├── mcp_server.py        # MCP protocol handler
│   ├── terminal_manager.py  # Terminal management (2600+ lines)
│   ├── web_server.py        # FastAPI + WebSocket
│   └── static/              # Web UI (xterm.js)
├── docs/                    # Documentation
├── examples/                # Usage examples
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## 🔧 Troubleshooting

### Web Interface Not Opening

**Solution**: Visit `http://localhost:8000` manually

### Port Already in Use

**Solution**: 
1. Auto-finds next available port
2. Or click shutdown in existing interface

### AI Keeps Using Single Tools

**Solution**: 
1. Restart IDE (MCP caches tool definitions)
2. Check tool descriptions loaded correctly

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/ai-mcp-terminal/
- **GitHub**: https://github.com/kanniganfan/ai-mcp-terminal
- **Issues**: https://github.com/kanniganfan/ai-mcp-terminal/issues

---

**Made with ❤️ for AI Assistants**

If this helps you, please give it a ⭐ star!
