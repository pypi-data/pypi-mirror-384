// AI-MCP Terminal Web Client

// 国际化翻译
const translations = {
    zh: {
        title: 'AI-MCP 终端',
        memory: '内存',
        running: '运行中',
        idle: '空闲',
        total: '总数',
        shutdown: '结束服务',
        terminalList: '终端列表',
        newTerminal: '+ 新建',
        selectTerminal: '选择一个终端',
        clearScreen: '清屏',
        endTerminal: '结束',
        inputPlaceholder: '输入命令...按Enter执行',
        execute: '执行',
        connected: '已连接到服务器',
        disconnected: '连接已断开，3秒后重连...',
        connectionError: '连接错误',
        aiExecuting: 'AI执行',
        shutdownConfirm: '确定要关闭Web终端服务吗？\n\n这将：\n✅ 终止所有终端进程\n✅ 释放端口和资源\n✅ MCP服务继续运行\n\n下次AI调用时会重新启动Web界面。',
        serverShuttingDown: 'Web服务正在关闭，资源正在释放...',
        shutdownSuccess: 'Web服务已关闭！MCP继续运行，下次AI调用时会重新启动。'
    },
    en: {
        title: 'AI-MCP Terminal',
        memory: 'Memory',
        running: 'Running',
        idle: 'Idle',
        total: 'Total',
        shutdown: 'Shutdown',
        terminalList: 'Terminal List',
        newTerminal: '+ New',
        selectTerminal: 'Select a terminal',
        clearScreen: 'Clear',
        endTerminal: 'Kill',
        inputPlaceholder: 'Type command... Press Enter to execute',
        execute: 'Execute',
        connected: 'Connected to server',
        disconnected: 'Disconnected, reconnecting in 3s...',
        connectionError: 'Connection error',
        aiExecuting: 'AI executing',
        shutdownConfirm: 'Are you sure to shutdown Web terminal service?\n\nThis will:\n✅ Terminate all terminal processes\n✅ Release ports and resources\n✅ Keep MCP service running\n\nWeb UI will restart on next AI call.',
        serverShuttingDown: 'Web service is shutting down, releasing resources...',
        shutdownSuccess: 'Web service closed! MCP continues running, will restart on next AI call.'
    }
};

let currentLang = localStorage.getItem('lang') || (navigator.language.startsWith('zh') ? 'zh' : 'en');

function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('lang', currentLang);
    updateLanguage();
}

function t(key) {
    return translations[currentLang][key] || key;
}

function updateLanguage() {
    // 更新所有带data-zh/data-en的元素
    document.querySelectorAll('[data-zh]').forEach(el => {
        const text = currentLang === 'zh' ? el.dataset.zh : el.dataset.en;
        if (text) el.textContent = text;
    });
    
    // 更新语言按钮
    document.getElementById('lang-text').textContent = currentLang === 'zh' ? 'EN' : '中文';
    
    // 更新标题
    document.querySelector('.header-left h1').textContent = t('title');
    document.querySelector('.sidebar-header h3').textContent = t('terminalList');
    
    // 更新按钮
    document.getElementById('new-terminal-btn').textContent = t('newTerminal');
    document.getElementById('clear-btn').textContent = t('clearScreen');
    document.getElementById('kill-btn').textContent = t('endTerminal');
    document.getElementById('execute-btn').textContent = t('execute');
    
    // 更新输入框placeholder
    document.getElementById('command-input').placeholder = t('inputPlaceholder');
    
    // 更新状态标签
    const statLabels = document.querySelectorAll('.stat-label');
    statLabels[0].textContent = t('memory');
    statLabels[1].textContent = t('running');
    statLabels[2].textContent = t('idle');
    statLabels[3].textContent = t('total');
}

class TerminalClient {
    constructor() {
        this.ws = null;
        this.terminals = new Map(); // session_id -> { term, element, fitAddon }
        this.sessions = new Map(); // session_id -> session data
        this.currentSessionId = null;
        this.currentTerminal = null;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.loadedHistory = new Set(); // 追踪已加载历史的终端
        
        this.init();
    }
    
    init() {
        updateLanguage(); // 初始化语言
        this.connectWebSocket();
        this.setupEventListeners();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('[WebSocket] Connected');
            this.showNotification(t('connected'), 'success');
            
            // 连接成功后，请求会话列表
            setTimeout(() => {
                this.requestSessionsList();
            }, 200);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification(t('connectionError'), 'error');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.showNotification(t('disconnected'), 'warning');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'init':
                this.updateStats(data.stats);
                this.updateSessionList(data.sessions);
                break;
                
            case 'stats_update':
                this.updateStats(data.stats);
                break;
                
            case 'session_created':
                this.addSession(data.session_id);
                this.requestSessionsList();
                // 自动展开新创建的终端
                setTimeout(() => this.selectSession(data.session_id), 100);
                break;
                
            case 'session_killed':
                this.removeSession(data.session_id);
                break;
                
            case 'command_started':
                this.handleCommandStarted(data);
                break;
            
            case 'output_chunk':
                this.handleOutputChunk(data);
                break;
                
            case 'command_completed':
                this.handleCommandCompleted(data);
                break;
                
            case 'command_error':
                this.handleCommandError(data);
                break;
                
            case 'server_shutdown':
                this.showNotification(data.message || '服务器正在关闭...', 'warning');
                // 关闭WebSocket
                if (this.ws) {
                    this.ws.close();
                }
                break;
        }
    }
    
    setupEventListeners() {
        // 命令历史记录
        this.commandHistory = [];
        this.historyIndex = -1;
        
        // 新建终端按钮
        document.getElementById('new-terminal-btn').addEventListener('click', () => {
            this.createNewSession();
        });
        
        // 执行命令按钮
        document.getElementById('execute-btn').addEventListener('click', () => {
            this.executeCommand();
        });
        
        const commandInput = document.getElementById('command-input');
        
        // 命令输入框快捷键支持
        commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.executeCommand();
            } else if (e.key === 'ArrowUp') {
                // ↑键：上一条历史命令
                e.preventDefault();
                if (this.commandHistory.length > 0) {
                    if (this.historyIndex === -1) {
                        this.historyIndex = this.commandHistory.length - 1;
                    } else if (this.historyIndex > 0) {
                        this.historyIndex--;
                    }
                    commandInput.value = this.commandHistory[this.historyIndex];
                }
            } else if (e.key === 'ArrowDown') {
                // ↓键：下一条历史命令
                e.preventDefault();
                if (this.historyIndex !== -1) {
                    this.historyIndex++;
                    if (this.historyIndex >= this.commandHistory.length) {
                        this.historyIndex = -1;
                        commandInput.value = '';
                    } else {
                        commandInput.value = this.commandHistory[this.historyIndex];
                    }
                }
            } else if (e.key === 'l' && e.ctrlKey) {
                // Ctrl+L：清屏
                e.preventDefault();
                if (this.currentTerminal) {
                    this.currentTerminal.clear();
                }
            }
        });
        
        // 清屏按钮
        document.getElementById('clear-btn').addEventListener('click', () => {
            if (this.currentTerminal) {
                this.currentTerminal.clear();
            }
        });
        
        // 结束终端按钮
        document.getElementById('kill-btn').addEventListener('click', () => {
            if (this.currentSessionId) {
                this.killSession(this.currentSessionId);
            }
        });
        
        // 结束服务按钮
        document.getElementById('shutdown-btn').addEventListener('click', async () => {
            if (confirm(t('shutdownConfirm'))) {
                try {
                    const response = await fetch('/api/shutdown', {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        this.showNotification(t('serverShuttingDown'), 'info');
                        
                        // 关闭WebSocket连接
                        if (this.ws) {
                            this.ws.close();
                        }
                        
                        // 2秒后显示完成提示
                        setTimeout(() => {
                            this.showNotification(t('shutdownSuccess'), 'success');
                            
                            // 再3秒后提示用户可以关闭页面
                            setTimeout(() => {
                                const msg = currentLang === 'zh' 
                                    ? '✅ Web服务已关闭\n✅ 端口和资源已释放\n✅ MCP服务继续运行\n\n您可以关闭此页面了。\n下次AI调用时会重新启动Web界面。'
                                    : '✅ Web service closed\n✅ Ports and resources released\n✅ MCP service still running\n\nYou can close this page now.\nWeb UI will restart on next AI call.';
                                alert(msg);
                            }, 3000);
                        }, 2000);
                    }
                } catch (error) {
                    console.error('关闭服务失败:', error);
                    this.showNotification(currentLang === 'zh' ? '关闭服务失败' : 'Shutdown failed', 'error');
                }
            }
        });
        
        // 定期更新统计信息和会话列表
        setInterval(() => {
            this.requestStats();
            this.requestSessionsList();
        }, 1000);
    }
    
    createNewSession() {
        const name = prompt('输入终端名称（可选）:');
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'create_session',
                name: name || undefined
            }));
        }
    }
    
    async selectSession(sessionId) {
        // 更新当前选择
        this.currentSessionId = sessionId;
        
        // 保存到localStorage，刷新后恢复
        localStorage.setItem('currentSessionId', sessionId);
        
        // 更新UI状态
        document.querySelectorAll('.terminal-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }
        
        // 显示/创建终端
        this.showTerminal(sessionId);
        
        // 更新标题
        const session = this.sessions.get(sessionId);
        if (session) {
            document.getElementById('current-terminal-title').textContent = 
                `${sessionId} (${session.shell_type})`;
        }
        
        // 显示输入区域
        document.getElementById('input-area').style.display = 'flex';
        
        // showTerminal 会处理历史加载，这里不需要重复加载
    }
    
    showTerminal(sessionId, autoCreate = false) {
        const container = document.getElementById('terminal-container');
        
        // 隐藏占位符
        const placeholder = container.querySelector('.terminal-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // 检查终端是否已存在
        const terminalExists = this.terminals.has(sessionId);
        
        // 只有非自动创建时才隐藏其他终端
        if (!autoCreate) {
            this.terminals.forEach((termObj, id) => {
                termObj.element.style.display = 'none';
            });
        }
        
        // 如果终端已存在，显示它（非自动创建时）
        if (terminalExists) {
            const termObj = this.terminals.get(sessionId);
            if (!autoCreate) {
                termObj.element.style.display = 'block';
                this.currentTerminal = termObj.term;
                termObj.fitAddon.fit();
            }
            
            // 如果刷新后还未加载历史，立即加载
            if (!this.loadedHistory.has(sessionId)) {
                console.log('[showTerminal] 终端已存在但未加载历史，立即加载, autoCreate:', autoCreate);
                setTimeout(async () => {
                    await this.fetchOutput(sessionId);
                    this.loadedHistory.add(sessionId);
                }, 100);
            } else {
                console.log('[showTerminal] 终端历史已加载，跳过');
            }
        } else {
            // 创建新终端
            const terminalDiv = document.createElement('div');
            terminalDiv.id = `terminal-${sessionId}`;
            container.appendChild(terminalDiv);
            
            const term = new Terminal({
                theme: {
                    background: '#1e1e1e',
                    foreground: '#d4d4d4',
                    cursor: '#d4d4d4',
                    black: '#000000',
                    red: '#f14c4c',
                    green: '#4ec9b0',
                    yellow: '#e5c07b',
                    blue: '#61afef',
                    magenta: '#c678dd',
                    cyan: '#56b6c2',
                    white: '#d4d4d4',
                    brightBlack: '#5a5a5a',
                    brightRed: '#f14c4c',
                    brightGreen: '#4ec9b0',
                    brightYellow: '#e5c07b',
                    brightBlue: '#61afef',
                    brightMagenta: '#c678dd',
                    brightCyan: '#56b6c2',
                    brightWhite: '#ffffff'
                },
                // 优化字体配置（解决中文字间距过大问题）
                fontFamily: '"Consolas", "Courier New", "Microsoft YaHei", "SimHei", monospace',
                fontSize: 14,
                fontWeight: 'normal',
                fontWeightBold: 'bold',
                letterSpacing: 0,
                lineHeight: 1.0,
                cursorBlink: true,
                cursorStyle: 'block',
                scrollback: 10000,
                convertEol: true,
                disableStdin: false,
                cols: 120,
                rows: 30,
                allowTransparency: false,
                // Windows模式优化
                windowsMode: true,
                // 允许提议的API
                allowProposedApi: false,
                // 禁用GPU加速（某些情况下会导致显示问题）
                rendererType: 'canvas'
            });
            
            // 终端内命令缓冲区
            let terminalCommandBuffer = '';
            
         // 监听终端输入
         term.onData(data => {
             // 处理回车
             if (data === '\r') {
                 term.write('\r\n');
                 if (terminalCommandBuffer.trim()) {
                     // 执行命令（标记为用户输入，不重复显示）
                     if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                         this.ws.send(JSON.stringify({
                             type: 'execute',
                             session_id: sessionId,
                             command: terminalCommandBuffer.trim(),
                             source: 'user'  // 标记来源：用户直接输入
                         }));
                     }
                     // 保存到历史
                     if (this.commandHistory[this.commandHistory.length - 1] !== terminalCommandBuffer.trim()) {
                         this.commandHistory.push(terminalCommandBuffer.trim());
                         if (this.commandHistory.length > 100) this.commandHistory.shift();
                     }
                     terminalCommandBuffer = '';
                 }
             }
            // 处理退格
            else if (data === '\u007F') {
                if (terminalCommandBuffer.length > 0) {
                    terminalCommandBuffer = terminalCommandBuffer.slice(0, -1);
                    term.write('\b \b');
                }
            }
            // 处理Ctrl+C（中断）
            else if (data === '\u0003') {
                term.write('^C\r\n');
                terminalCommandBuffer = '';
                // 发送中断信号到后端
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'interrupt',
                        session_id: sessionId
                    }));
                }
                // 显示新提示符
                const session = this.sessions.get(sessionId);
                const cwd = session?.cwd || '~';
                term.write(`\x1b[1;32m$\x1b[0m `);
            }
            // 处理Ctrl+L（清屏）
            else if (data === '\u000C') {
                term.clear();
                // 显示新提示符
                const session = this.sessions.get(sessionId);
                const cwd = session?.cwd || '~';
                term.write(`\x1b[1;32m$\x1b[0m `);
            }
            // 处理Ctrl+V（粘贴）
            else if (data === '\u0016') {
                // 从剪贴板粘贴
                navigator.clipboard.readText().then(text => {
                    terminalCommandBuffer += text;
                    term.write(text);
                }).catch(err => {
                    console.error('Failed to read clipboard:', err);
                });
            }
            // 普通字符
            else {
                terminalCommandBuffer += data;
                term.write(data);
            }
        });
            
            const fitAddon = new FitAddon.FitAddon();
            term.loadAddon(fitAddon);
            term.open(terminalDiv);
            fitAddon.fit();
            
            // 支持右键智能复制/粘贴
            terminalDiv.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                const selection = term.getSelection();
                
                if (selection) {
                    // 有选中文本 -> 复制
                    navigator.clipboard.writeText(selection).then(() => {
                        console.log('复制成功:', selection);
                        // 可选：显示复制成功提示
                        term.write('\r\n\x1b[32m✓ 已复制\x1b[0m\r\n');
                        setTimeout(() => {
                            term.write(`\x1b[1;32m$\x1b[0m `);
                        }, 500);
                    }).catch(err => {
                        console.error('Failed to copy:', err);
                    });
                } else {
                    // 无选中文本 -> 粘贴
                    navigator.clipboard.readText().then(text => {
                        terminalCommandBuffer += text;
                        term.write(text);
                    }).catch(err => {
                        console.error('Failed to paste:', err);
                    });
                }
            });
            
            // 支持Ctrl+Shift+C/V（标准终端快捷键）
            terminalDiv.addEventListener('keydown', (e) => {
                // Ctrl+Shift+C 复制选中内容
                if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                    e.preventDefault();
                    const selection = term.getSelection();
                    if (selection) {
                        navigator.clipboard.writeText(selection).catch(err => {
                            console.error('Failed to copy:', err);
                        });
                    }
                }
                // Ctrl+Shift+V 粘贴
                else if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                    e.preventDefault();
                    navigator.clipboard.readText().then(text => {
                        terminalCommandBuffer += text;
                        term.write(text);
                    }).catch(err => {
                        console.error('Failed to paste:', err);
                    });
                }
            });
            
            // 如果是自动创建（后台终端），初始设置为隐藏
            if (autoCreate) {
                terminalDiv.style.display = 'none';
            }
            
            // 保存包装对象
            const termObj = {
                term: term,
                element: terminalDiv,
                fitAddon: fitAddon
            };
            this.terminals.set(sessionId, termObj);
            
            // 只有非自动创建时才设置为当前终端
            if (!autoCreate) {
                this.currentTerminal = term;
            }
            
            // 监听窗口大小变化
            window.addEventListener('resize', () => {
                fitAddon.fit();
            });
            
            // 新创建的终端立即加载历史（无论autoCreate是否为true）
            if (!this.loadedHistory.has(sessionId)) {
                console.log('[showTerminal] 新终端创建，立即加载历史, autoCreate:', autoCreate);
                setTimeout(async () => {
                    await this.fetchOutput(sessionId);
                    this.loadedHistory.add(sessionId);
                }, 100);
            } else {
                console.log('[showTerminal] 终端已加载历史，跳过');
            }
        }
    }
    
    executeCommand() {
        const input = document.getElementById('command-input');
        const command = input.value.trim();
        
        if (!command || !this.currentSessionId) return;
        
        // 保存到命令历史
        if (this.commandHistory[this.commandHistory.length - 1] !== command) {
            this.commandHistory.push(command);
            // 限制历史记录数量
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
        }
        this.historyIndex = -1; // 重置历史索引
        
        // 发送命令（不在这里显示，等command_started事件）
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'execute',
                session_id: this.currentSessionId,
                command: command
            }));
        }
        
        // 清空输入
        input.value = '';
    }
    
    killSession(sessionId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'kill_session',
                session_id: sessionId
            }));
        }
    }
    
    removeSession(sessionId) {
        console.log('[removeSession] 删除终端:', sessionId);
        console.log('[removeSession] 删除前终端列表:', Array.from(this.terminals.keys()));
        console.log('[removeSession] 删除前会话列表:', Array.from(this.sessions.keys()));
        
        // 1. 移除终端实例
        if (this.terminals.has(sessionId)) {
            const termObj = this.terminals.get(sessionId);
            try {
                termObj.term.dispose();
                termObj.element.remove();
            } catch (e) {
                console.error('[removeSession] 清理终端实例失败:', e);
            }
            this.terminals.delete(sessionId);
            console.log('[removeSession] ✅ 已删除终端实例');
        }
        
        // 2. 移除会话数据
        this.sessions.delete(sessionId);
        console.log('[removeSession] ✅ 已删除会话数据');
        
        // 3. 清理历史加载记录
        this.loadedHistory.delete(sessionId);
        console.log('[removeSession] ✅ 已清理历史记录标记');
        
        // 4. 移除UI元素
        const item = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (item) {
            item.remove();
            console.log('[removeSession] ✅ 已删除UI元素');
        }
        
        // 5. 如果是当前会话，需要选择其他终端
        const wasCurrentSession = this.currentSessionId === sessionId;
        if (wasCurrentSession) {
            console.log('[removeSession] 删除的是当前会话，准备选择其他终端');
            this.currentSessionId = null;
            this.currentTerminal = null;
            
            // 清理localStorage中的记录
            const savedSessionId = localStorage.getItem('currentSessionId');
            if (savedSessionId === sessionId) {
                localStorage.removeItem('currentSessionId');
                console.log('[removeSession] ✅ 已清理localStorage');
            }
            
            // 隐藏所有终端，显示占位符（不要清空container，避免删除其他终端的DOM）
            const container = document.getElementById('terminal-container');
            this.terminals.forEach((termObj, id) => {
                termObj.element.style.display = 'none';
            });
            
            // 检查是否有占位符，没有则添加
            let placeholder = container.querySelector('.terminal-placeholder');
            if (!placeholder) {
                placeholder = document.createElement('div');
                placeholder.className = 'terminal-placeholder';
                placeholder.innerHTML = '<p>👈 从左侧选择或创建一个终端会话</p>';
                container.appendChild(placeholder);
            }
            placeholder.style.display = 'block';
            
            document.getElementById('input-area').style.display = 'none';
        }
        
        console.log('[removeSession] 删除后终端列表:', Array.from(this.terminals.keys()));
        console.log('[removeSession] 删除后会话列表:', Array.from(this.sessions.keys()));
        
        // 6. 刷新会话列表
        this.requestSessionsList().then(() => {
            console.log('[removeSession] 会话列表已刷新');
            
            // 如果删除的是当前会话，且还有其他会话，确保自动选择
            if (wasCurrentSession && this.sessions.size > 0 && !this.currentSessionId) {
                console.log('[removeSession] 强制选择第一个剩余会话');
                const firstSessionId = Array.from(this.sessions.keys())[0];
                setTimeout(() => {
                    this.selectSession(firstSessionId);
                }, 100);
            }
        });
    }
    
    addSession(sessionId) {
        this.requestSessionsList();
    }
    
    updateSessionList(sessions) {
        sessions.forEach(session => {
            this.sessions.set(session.session_id, session);
        });
        
        const listContainer = document.getElementById('terminal-list');
        listContainer.innerHTML = '';
        
        sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = 'terminal-item';
            item.dataset.sessionId = session.session_id;
            
            // 保持当前选中状态
            if (session.session_id === this.currentSessionId) {
                item.classList.add('active');
            }
            
            const statusClass = `status-${session.status}`;
            const statusText = {
                'running': '运行中',
                'idle': '空闲',
                'completed': '已完成'
            }[session.status] || session.status;
            
            // Shell类型图标
            const shellIcon = {
                'wsl': '🐧',        // WSL bash (企鹅 - Linux标志)
                'bash': '🐚',       // Git Bash (贝壳)
                'zsh': '⚡',
                'fish': '🐟',
                'powershell': '⚙️',
                'pwsh': '💠',
                'cmd': '📟',
                'sh': '🔧'
            }[session.shell_type] || '💻';
            
            item.innerHTML = `
                <div class="terminal-item-header">
                    <span class="terminal-name">${shellIcon} ${session.session_id}</span>
                    <span class="terminal-status ${statusClass}">${statusText}</span>
                </div>
                <div class="terminal-info">${session.shell_type} | ${session.cwd || '~'}</div>
            `;
            
            item.addEventListener('click', () => {
                this.selectSession(session.session_id);
            });
            
            listContainer.appendChild(item);
        });
        
        // 如果有会话且当前没有选中，尝试恢复之前选中的或选择第一个
        // 使用标志防止重复选择
        if (sessions.length > 0 && !this.currentSessionId && !this._autoSelectInProgress) {
            this._autoSelectInProgress = true;
            
            // 尝试从localStorage恢复之前选中的终端
            const savedSessionId = localStorage.getItem('currentSessionId');
            const sessionExists = savedSessionId && sessions.some(s => s.session_id === savedSessionId);
            
            const sessionToSelect = sessionExists ? savedSessionId : sessions[0].session_id;
            console.log('[updateSessionList] 自动选择会话:', sessionToSelect, '(恢复:', sessionExists, ')');
            
            setTimeout(() => {
                this.selectSession(sessionToSelect);
                this._autoSelectInProgress = false;
            }, 300);
        }
    }
    
    updateStats(stats) {
        document.getElementById('memory-usage').textContent = `${stats.memory_percent.toFixed(1)}%`;
        document.getElementById('running-count').textContent = stats.running;
        document.getElementById('idle-count').textContent = stats.idle;
        document.getElementById('total-count').textContent = stats.total_sessions;
        
        // 内存警告
        const memoryEl = document.getElementById('memory-usage');
        if (stats.memory_percent >= 95) {
            memoryEl.classList.add('memory-warning');
        } else {
            memoryEl.classList.remove('memory-warning');
        }
    }
    
    handleCommandStarted(data) {
        console.log('[实时] 命令执行:', data.command, '来源:', data.source, '终端:', data.session_id);
        
        // 检查会话是否仍然存在（可能已被删除）
        if (!this.sessions.has(data.session_id)) {
            console.log('[命令开始] 会话已被删除，忽略事件:', data.session_id);
            return;
        }
        
        // 支持后台终端显示命令
        let termObj = this.terminals.get(data.session_id);
        
        // 如果终端不存在，自动创建（后台终端）
        if (!termObj) {
            console.log('[命令开始] 终端不存在，自动创建:', data.session_id);
            this.showTerminal(data.session_id, true);  // autoCreate = true
            termObj = this.terminals.get(data.session_id);
        }
        
        if (termObj) {
            // 获取会话信息
            const session = this.sessions.get(data.session_id);
            const cwd = session?.cwd || '~';
            
            // 只有AI执行的命令才显示（用户直接输入的已经在本地显示了）
            if (data.source !== 'user') {
                // 实时显示命令（带AI标识）
                const aiTag = '\x1b[1;33m[AI]\x1b[0m ';
                const prompt = `\x1b[1;32muser@ai-mcp\x1b[0m:\x1b[1;34m${cwd}\x1b[0m$ `;
                termObj.term.writeln(aiTag + prompt + data.command);
                
                // 只有当前终端才显示通知
                if (this.currentSessionId === data.session_id) {
                    this.showNotification(`${t('aiExecuting')}: ${data.command}`, 'info');
                }
            }
        }
        
        // 刷新会话列表以更新状态
        this.requestSessionsList();
    }
    
    handleOutputChunk(data) {
        console.log('[实时输出] 收到chunk:', data.session_id, data.stream, data.chunk.substring(0, 50));
        
        // 检查会话是否仍然存在（可能已被删除）
        if (!this.sessions.has(data.session_id)) {
            console.log('[实时输出] 会话已被删除，忽略输出:', data.session_id);
            return;
        }
        
        // 实时显示输出块（支持后台终端）
        let termObj = this.terminals.get(data.session_id);
        
        // 如果终端不存在，自动创建（后台终端）
        if (!termObj) {
            console.log('[实时输出] 终端不存在，自动创建:', data.session_id);
            this.showTerminal(data.session_id, true);  // autoCreate = true
            termObj = this.terminals.get(data.session_id);
        }
        
        if (termObj) {
            const chunk = data.chunk;
            const stream = data.stream;
            
            // 直接写入（后端已完善智能解码）
            try {
                // 根据stream类型设置颜色
                if (stream === 'stderr') {
                    termObj.term.write(`\x1b[31m${chunk}\x1b[0m`);
                } else {
                    termObj.term.write(chunk);
                }
            } catch (e) {
                console.error('[实时输出] 写入错误:', e, 'chunk:', chunk);
            }
        } else {
            console.warn('[实时输出] 创建终端失败:', data.session_id);
        }
    }
    
    handleCommandCompleted(data) {
        // 检查会话是否仍然存在（可能已被删除）
        if (!this.sessions.has(data.session_id)) {
            console.log('[命令完成] 会话已被删除，忽略事件:', data.session_id);
            return;
        }
        
        // 支持后台终端完成命令
        let termObj = this.terminals.get(data.session_id);
        
        // 如果终端不存在，自动创建（后台终端）
        if (!termObj) {
            console.log('[命令完成] 终端不存在，自动创建:', data.session_id);
            this.showTerminal(data.session_id, true);  // autoCreate = true
            termObj = this.terminals.get(data.session_id);
        }
        
        if (termObj) {
            // 显示stderr（如果有）
            if (data.stderr) {
                termObj.term.write(`\x1b[31m${data.stderr}\x1b[0m`);
                if (!data.stderr.endsWith('\n')) {
                    termObj.term.writeln('');
                }
            }
            
            // 退出码（只显示致命错误，跳过128等常见错误码）
            if (data.returncode !== undefined && data.returncode !== 0) {
                // 128: 无效参数（常见于git等命令）
                // 1: 一般错误
                // 只显示真正需要注意的错误码
                const ignoreCodes = [128, 1, 130]; // 130是Ctrl+C
                if (!ignoreCodes.includes(data.returncode)) {
                    termObj.term.writeln(`\x1b[31m[Exit code: ${data.returncode}]\x1b[0m`);
                }
            }
            
            // 添加新提示符
            const session = this.sessions.get(data.session_id);
            const cwd = session?.cwd || '~';
            termObj.term.write(`\x1b[1;32m$\x1b[0m `);
        }
        
        this.requestSessionsList();
    }
    
    handleCommandError(data) {
        // 检查会话是否仍然存在（可能已被删除）
        if (!this.sessions.has(data.session_id)) {
            console.log('[命令错误] 会话已被删除，忽略事件:', data.session_id);
            return;
        }
        
        // 支持后台终端显示错误
        let termObj = this.terminals.get(data.session_id);
        
        // 如果终端不存在，自动创建（后台终端）
        if (!termObj) {
            console.log('[命令错误] 终端不存在，自动创建:', data.session_id);
            this.showTerminal(data.session_id, true);  // autoCreate = true
            termObj = this.terminals.get(data.session_id);
        }
        
        if (termObj) {
            termObj.term.writeln(`\x1b[31m错误: ${data.error}\x1b[0m`);
        }
    }
    
    async fetchOutput(sessionId) {
        try {
            console.log(`[fetchOutput] 开始获取会话 ${sessionId} 的历史输出...`);
            const response = await fetch(`/api/sessions/${sessionId}/output?lines=1000`);
            const data = await response.json();
            
            console.log(`[fetchOutput] 会话 ${sessionId} API响应:`, data);
            console.log(`[fetchOutput] success: ${data.success}, 输出数组长度: ${data.output ? data.output.length : 0}`);
            
            const termObj = this.terminals.get(sessionId);
            console.log(`[fetchOutput] 终端对象存在: ${!!termObj}`);
            
            // 检查success字段和output数组
            if (!data.success) {
                console.warn('[fetchOutput] API返回失败:', data);
                return;
            }
            
            if (data.output && data.output.length > 0 && termObj) {
                console.log(`[fetchOutput] 显示 ${data.output.length} 条历史记录`);
                
                const terminal = termObj.term;
                
                // 获取会话信息用于显示路径
                const session = this.sessions.get(sessionId);
                const cwd = session?.cwd || '~';
                
                data.output.forEach((item, index) => {
                    // 调试日志：显示每一项的内容
                    console.log(`[fetchOutput] 处理第${index+1}条: command=${item?.command}, output长度=${item?.output?.length || 0}, returncode=${item?.returncode}`);
                    
                    // 跳过空项（但放宽检查）
                    if (!item) {
                        console.warn('[fetchOutput] 跳过null/undefined项:', item);
                        return;
                    }
                    
                    // 如果没有command字段，可能是旧格式或异常，尝试显示
                    if (!item.command) {
                        console.warn('[fetchOutput] 项缺少command字段，尝试显示output:', item);
                        if (item.output) {
                            terminal.write(item.output);
                            if (!item.output.endsWith('\n')) {
                                terminal.writeln('');
                            }
                        }
                        return;
                    }
                    
                    // 显示命令（带提示符）
                    const prompt = `\x1b[1;32muser@ai-mcp\x1b[0m:\x1b[1;34m${cwd}\x1b[0m$ `;
                    terminal.writeln(prompt + item.command);
                    
                    // 显示输出（错误时用红色）
                    if (item.output) {
                        // 如果返回码为-1（异常），用红色显示错误信息
                        if (item.returncode === -1) {
                            terminal.write(`\x1b[31m${item.output}\x1b[0m`);
                        } else {
                            terminal.write(item.output);
                        }
                        if (!item.output.endsWith('\n')) {
                            terminal.writeln('');
                        }
                    }
                    
                    // 如果是运行中的命令，显示"运行中..."
                    if (item.is_running) {
                        terminal.write(`\x1b[33m[运行中...]\x1b[0m `);
                    }
                    // 如果有错误分类，显示详细错误信息
                    else if (item.error_category && item.error_description) {
                        // 根据错误类型选择不同的颜色
                        const errorColors = {
                            'COMMAND_NOT_FOUND': '\x1b[33m',  // 黄色
                            'PERMISSION_DENIED': '\x1b[31m',   // 红色
                            'FILE_NOT_FOUND': '\x1b[33m',      // 黄色
                            'SYNTAX_ERROR': '\x1b[35m',        // 紫色
                            'USER_INTERRUPTED': '\x1b[90m',    // 灰色
                            'INVALID_ARGUMENT': '\x1b[33m',    // 黄色
                            'GENERAL_ERROR': '\x1b[31m'        // 红色
                        };
                        const color = errorColors[item.error_category] || '\x1b[31m';
                        terminal.writeln(`${color}[${item.error_category}] ${item.error_description}\x1b[0m`);
                    }
                    // 如果有错误码但没有分类，只显示重要的（忽略128/1/130）
                    else if (item.returncode !== undefined && item.returncode !== 0) {
                        const ignoreCodes = [128, 1, 130];
                        if (!ignoreCodes.includes(item.returncode)) {
                            terminal.writeln(`\x1b[31m[退出码: ${item.returncode}]\x1b[0m`);
                        }
                    }
                });
                
                // 添加当前提示符
                const prompt = `\x1b[1;32m$\x1b[0m `;
                terminal.write(prompt);
            } else {
                console.log(`[fetchOutput] 无历史输出或终端不存在`);
            }
        } catch (error) {
            console.error('[fetchOutput] 获取输出失败:', error);
        }
    }
    
    requestStats() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'request_stats' }));
        }
    }
    
    async requestSessionsList() {
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            this.updateSessionList(data.sessions);
        } catch (error) {
            console.error('获取会话列表失败:', error);
        }
    }
    
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 创建通知元素
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;
        
        // 根据类型设置颜色
        const colors = {
            'success': '#4ec9b0',
            'error': '#f14c4c',
            'warning': '#e5c07b',
            'info': '#61afef'
        };
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.terminalClient = new TerminalClient();
});

