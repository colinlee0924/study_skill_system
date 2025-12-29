/**
 * Claude Skills 可视化前端应用
 *
 * 功能：
 * 1. API Key 配置与本地存储
 * 2. Skill 详情展示
 * 3. 用户友好的事件解释
 * 4. 科技感 UI 交互
 */

// ==================== 全局状态 ====================
let ws = null;
let isProcessing = false;
let reconnectAttempts = 0;
let skillsData = {};  // 存储 skill 详情
const MAX_RECONNECT_ATTEMPTS = 5;

// ==================== 配置管理 ====================

function loadConfig() {
    return {
        apiKey: localStorage.getItem('deepseek_api_key') || '',
        model: localStorage.getItem('deepseek_model') || 'deepseek-reasoner'
    };
}

function saveConfigToStorage(apiKey, model) {
    localStorage.setItem('deepseek_api_key', apiKey);
    localStorage.setItem('deepseek_model', model);
}

function showConfigModal() {
    const config = loadConfig();
    document.getElementById('apiKeyInput').value = config.apiKey;
    document.getElementById('modelSelect').value = config.model;
    document.getElementById('configModal').style.display = 'flex';
}

function hideConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

function togglePassword() {
    const input = document.getElementById('apiKeyInput');
    const eyeIcon = document.getElementById('eyeIcon');

    if (input.type === 'password') {
        input.type = 'text';
        eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
    } else {
        input.type = 'password';
        eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
    }
}

function saveConfig() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    const model = document.getElementById('modelSelect').value;

    if (!apiKey) {
        showNotification('请输入您的 API 密钥', 'error');
        return;
    }

    if (!apiKey.startsWith('sk-')) {
        showNotification('API 密钥应以 "sk-" 开头', 'error');
        return;
    }

    saveConfigToStorage(apiKey, model);
    hideConfigModal();

    // 更新模型显示
    document.getElementById('modelName').textContent = model === 'deepseek-reasoner' ? 'DeepSeek Reasoner' : 'DeepSeek Chat';

    // 初始化 Agent
    initAgent(apiKey, model);
}

// ==================== 通知系统 ====================

function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <span class="notification-text">${message}</span>
    `;

    document.body.appendChild(notification);

    // 动画显示
    setTimeout(() => notification.classList.add('show'), 10);

    // 自动消失
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== Skill 详情弹窗 ====================

function showSkillModal(skillName) {
    const skill = skillsData[skillName];
    if (!skill) {
        showNotification('技能详情暂不可用，请等待初始化完成', 'error');
        return;
    }

    // 设置图标
    const iconMap = {
        'data_analysis': '📊',
        'pdf_processing': '📄',
        'text_processing': '📝',
        'file_operations': '📁',
        'web_search': '🔍',
        'code_execution': '💻',
        'default': '🔧'
    };

    document.getElementById('skillModalIcon').textContent = iconMap[skillName] || iconMap.default;
    document.getElementById('skillModalTitle').textContent = skill.name || skillName;
    document.getElementById('skillModalDesc').textContent = skill.description || '暂无描述';

    // 设置元信息
    document.getElementById('skillModalVersion').textContent = skill.version || '1.0.0';
    document.getElementById('skillModalAuthor').textContent = skill.author || '-';

    // 渲染标签
    const tagsEl = document.getElementById('skillModalTags');
    if (skill.tags && skill.tags.length > 0) {
        tagsEl.innerHTML = skill.tags.map(tag =>
            `<span class="skill-tag-item">${escapeHtml(tag)}</span>`
        ).join('');
    } else {
        tagsEl.innerHTML = '';
    }

    // 渲染工具列表
    const toolsEl = document.getElementById('skillModalTools');
    const toolCountEl = document.getElementById('skillToolCount');
    if (skill.tools && skill.tools.length > 0) {
        toolCountEl.textContent = skill.tools.length;
        toolsEl.innerHTML = skill.tools.map(tool => `
            <div class="skill-tool-item">
                <div class="skill-tool-header">
                    <span class="skill-tool-icon">⚡</span>
                    <span class="skill-tool-name">${escapeHtml(tool.name || tool)}</span>
                </div>
                ${tool.description ? `<div class="skill-tool-desc">${escapeHtml(tool.description)}</div>` : ''}
            </div>
        `).join('');
    } else {
        toolCountEl.textContent = '0';
        toolsEl.innerHTML = '<p class="empty-text">暂无定义的工具</p>';
    }

    // 渲染 instructions（默认折叠）
    const instructionsEl = document.getElementById('skillModalInstructions');
    if (skill.instructions) {
        instructionsEl.innerHTML = formatInstructions(skill.instructions);
    } else {
        instructionsEl.innerHTML = '<p class="empty-text">暂无使用说明</p>';
    }
    instructionsEl.style.display = 'none';
    document.getElementById('instructionsCollapseIcon').textContent = '▼';

    document.getElementById('skillModal').style.display = 'flex';
}

function toggleInstructions() {
    const el = document.getElementById('skillModalInstructions');
    const icon = document.getElementById('instructionsCollapseIcon');
    if (el.style.display === 'none') {
        el.style.display = 'block';
        icon.textContent = '▲';
    } else {
        el.style.display = 'none';
        icon.textContent = '▼';
    }
}

function closeSkillModal() {
    document.getElementById('skillModal').style.display = 'none';
}

function formatInstructions(text) {
    if (!text) return '';

    return escapeHtml(text)
        .replace(/^## (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h5>$1</h5>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// ==================== 粒子背景效果 ====================

function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        container.appendChild(particle);
    }
}

// ==================== WebSocket 连接 ====================

function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        updateConnectionStatus(true);
        addEvent('connection', '系统', '连接成功', '已成功建立 WebSocket 连接');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);

        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(connect, 3000);
            addEvent('connection', '系统', '连接断开', `3秒后重新连接... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addEvent('error', '系统', '连接错误', '无法连接到服务器');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    const textEl = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.className = 'connection-status connected';
        textEl.textContent = '已连接';
    } else {
        statusEl.className = 'connection-status disconnected';
        textEl.textContent = '未连接';
    }
}

// ==================== 消息处理 ====================

function handleMessage(data) {
    console.log('Received:', data);

    switch (data.type) {
        case 'init':
            handleInit(data);
            break;

        case 'agent_ready':
            handleAgentReady(data);
            break;

        case 'skills_info':
            handleSkillsInfo(data);
            break;

        case 'status':
            addEvent('status', '系统', data.status || '状态更新', data.message);
            break;

        case 'user_message':
            addUserMessage(data.content);
            setFlowStep(1);
            break;

        case 'processing_start':
            handleProcessingStart();
            break;

        case 'middleware_filter':
            handleMiddlewareFilter(data);
            break;

        case 'log':
            handleLog(data);
            break;

        case 'ai_response':
            handleAIResponse(data);
            break;

        case 'processing_end':
            handleProcessingEnd();
            break;

        case 'error':
            handleError(data);
            break;
    }
}

function handleInit(data) {
    addEvent('connection', '系统', '初始化完成', '系统就绪，请配置 API 设置');

    // 检查是否已有配置
    const config = loadConfig();
    if (!config.apiKey) {
        showConfigModal();
    } else {
        // 自动初始化
        document.getElementById('modelName').textContent =
            config.model === 'deepseek-reasoner' ? 'DeepSeek Reasoner' : 'DeepSeek Chat';
        initAgent(config.apiKey, config.model);
    }
}

function handleAgentReady(data) {
    // 存储 skills 数据
    if (data.skills_info) {
        skillsData = data.skills_info;
    }

    // 更新已注册的 Skills - 可点击
    const registeredEl = document.getElementById('registeredSkills');
    if (data.skills && data.skills.length > 0) {
        registeredEl.innerHTML = data.skills.map(s =>
            `<span class="skill-tag" onclick="showSkillModal('${escapeHtml(s)}')" title="点击查看详情">${escapeHtml(s)}</span>`
        ).join('');
    }

    // 更新工具计数
    updateToolsDisplay(2, 0);  // 初始只有 loader 工具

    // 更新头部统计
    document.getElementById('headerToolCount').textContent = '2';
    document.getElementById('headerSkillCount').textContent = data.skills ? data.skills.length : '0';

    // 启用输入
    document.getElementById('chatInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;

    // 更新初始化按钮
    const initBtn = document.getElementById('initBtn');
    initBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>系统就绪</span>
    `;
    initBtn.classList.add('ready');

    addEvent('success', 'Agent', '初始化完成',
        `已加载 ${data.skills ? data.skills.length : 0} 个技能，${data.total_tools || 2} 个基础工具`);
}

function handleSkillsInfo(data) {
    if (data.skills) {
        skillsData = data.skills;
    }
}

function handleProcessingStart() {
    isProcessing = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = `
        <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
        </svg>
    `;

    addEvent('processing', '处理流程', '开始处理', '正在分析您的请求...');
}

function handleMiddlewareFilter(data) {
    setFlowStep(2);

    if (data.skills_loaded) {
        const skills = parseSkillsList(data.skills_loaded);

        // 更新已加载的 Skills 显示
        const loadedEl = document.getElementById('loadedSkills');
        if (skills.length > 0) {
            loadedEl.innerHTML = skills.map(s =>
                `<span class="skill-tag loaded" onclick="showSkillModal('${escapeHtml(s)}')">${escapeHtml(s)}</span>`
            ).join('');
        }

        addEvent('middleware', '技能加载器', '技能已激活',
            `动态加载了 ${skills.length} 个技能: ${skills.join(', ')}`);
    }

    if (data.filtered_tools) {
        const { count, tools } = parseToolsInfo(data.filtered_tools);
        updateToolsDisplay(count, tools.length - 2);  // 减去 loader 工具

        addEvent('middleware', '工具过滤器', '工具已配置',
            `当前任务可用 ${count} 个工具`);
    }
}

function handleLog(data) {
    // 解析日志并转换为用户友好的中文消息
    const message = data.message;
    const logger = data.logger || '';

    // 工具名称中英对照
    const toolNameMap = {
        'load_skill': '加载技能',
        'list_skills': '列出技能',
        'calculate_statistics': '计算统计',
        'analyze_data': '分析数据',
        'process_text': '处理文本',
        'extract_keywords': '提取关键词'
    };

    // 翻译工具名称
    function translateToolName(name) {
        return toolNameMap[name] || name;
    }

    if (message.includes('tool_calls')) {
        setFlowStep(3);
        addEvent('execution', 'Agent', '工具调用', 'AI 正在调用工具来完成您的请求');
    } else if (message.includes('Invoking')) {
        const toolMatch = message.match(/Invoking: (\w+)/);
        if (toolMatch) {
            const toolName = toolMatch[1];
            const translatedName = translateToolName(toolName);
            addEvent('tool', '执行中', `正在运行: ${translatedName}`, `调用 ${toolName} 工具处理中...`);
        }
    } else if (message.includes('SkillMiddleware')) {
        // Middleware 相关日志已在 handleMiddlewareFilter 中处理
        // 这里处理其他 middleware 日志
        if (message.includes('Processing') || message.includes('processing')) {
            addEvent('middleware', '中间件', '处理中', '正在进行工具过滤...');
        }
    } else if (message.includes('Agent')) {
        // Agent 相关日志
        if (message.includes('thinking') || message.includes('Thinking')) {
            addEvent('processing', 'Agent', '思考中', 'AI 正在分析问题...');
        }
    }
}

function handleAIResponse(data) {
    setFlowStep(5);
    addAIMessage(data.content, data.reasoning, data.tool_calls);

    // 更新加载的 skills
    if (data.skills_loaded && data.skills_loaded.length > 0) {
        setFlowStep(4);
        const loadedEl = document.getElementById('loadedSkills');
        loadedEl.innerHTML = data.skills_loaded.map(s =>
            `<span class="skill-tag loaded" onclick="showSkillModal('${escapeHtml(s)}')">${escapeHtml(s)}</span>`
        ).join('');
    }

    addEvent('success', '响应', '任务完成', 'AI 已完成您的请求处理');
}

function handleProcessingEnd() {
    isProcessing = false;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = false;
    sendBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
    `;
    setTimeout(() => resetFlowSteps(), 2000);
}

function handleError(data) {
    addEvent('error', '错误', '出现问题', data.message);
    addSystemMessage(`❌ ${data.message}`);
    isProcessing = false;

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = false;
    sendBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
    `;
}

// ==================== UI 更新函数 ====================

function parseSkillsList(skillsStr) {
    const match = skillsStr.match(/\[([^\]]*)\]/);
    if (match) {
        return match[1].split(',')
            .map(s => s.trim().replace(/'/g, ''))
            .filter(s => s);
    }
    return [];
}

function parseToolsInfo(toolsStr) {
    const countMatch = toolsStr.match(/\((\d+)\)/);
    const toolsMatch = toolsStr.match(/\[([^\]]*)\]/);

    const count = countMatch ? parseInt(countMatch[1]) : 0;
    const tools = toolsMatch ? toolsMatch[1].split(',')
        .map(s => s.trim().replace(/'/g, ''))
        .filter(s => s) : [];

    return { count, tools };
}

function updateToolsDisplay(count, skillToolsCount) {
    // 更新圆环
    const ring = document.getElementById('toolsRing');
    const circumference = 2 * Math.PI * 45;
    const progress = Math.min(count / 10, 1);  // 假设最大10个工具
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference * (1 - progress);

    // 更新数字
    document.getElementById('toolsCount').textContent = count;
    document.getElementById('headerToolCount').textContent = count;

    // 更新分解
    const breakdownEl = document.getElementById('toolsBreakdown');
    breakdownEl.innerHTML = `
        <div class="breakdown-item">
            <span class="dot loader"></span>
            <span>加载器: 2</span>
        </div>
        <div class="breakdown-item">
            <span class="dot skill"></span>
            <span>技能工具: ${skillToolsCount}</span>
        </div>
    `;
}

function setFlowStep(step) {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step${i}`);
        if (el) {
            el.classList.toggle('active', i <= step);
            el.classList.toggle('current', i === step);
        }
    }
}

function resetFlowSteps() {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step${i}`);
        if (el) {
            el.classList.remove('active', 'current');
        }
    }
}

// ==================== 事件渲染 (用户友好版) ====================

function addEvent(type, source, title, description) {
    const eventsList = document.getElementById('eventsList');
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });

    // 移除欢迎消息
    const welcome = eventsList.querySelector('.event-welcome');
    if (welcome) welcome.remove();

    // 类型配置：图标、颜色、中文标签
    const typeConfig = {
        'connection': { icon: '🔗', label: '连接', color: 'primary' },
        'success': { icon: '✅', label: '成功', color: 'success' },
        'error': { icon: '❌', label: '错误', color: 'error' },
        'middleware': { icon: '⚙️', label: '过滤', color: 'middleware' },
        'processing': { icon: '⏳', label: '处理', color: 'processing' },
        'execution': { icon: '🚀', label: '执行', color: 'execution' },
        'tool': { icon: '🔧', label: '工具', color: 'tool' },
        'status': { icon: '💬', label: '消息', color: 'status' }
    };

    const config = typeConfig[type] || { icon: '📌', label: '事件', color: 'info' };

    const eventHtml = `
        <div class="event-item ${config.color}">
            <div class="event-timeline">
                <div class="event-dot"></div>
                <div class="event-line"></div>
            </div>
            <div class="event-content">
                <div class="event-header">
                    <span class="event-icon">${config.icon}</span>
                    <span class="event-label">${config.label}</span>
                    <span class="event-time">${time}</span>
                </div>
                <div class="event-title">${escapeHtml(title)}</div>
                ${description ? `<div class="event-desc">${escapeHtml(description)}</div>` : ''}
            </div>
        </div>
    `;

    eventsList.insertAdjacentHTML('afterbegin', eventHtml);

    // 限制事件数量
    while (eventsList.children.length > 50) {
        eventsList.removeChild(eventsList.lastChild);
    }
}

// ==================== 消息渲染 ====================

function addUserMessage(content) {
    const messagesDiv = document.getElementById('chatMessages');

    // 移除欢迎消息
    const welcome = messagesDiv.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    messagesDiv.innerHTML += `
        <div class="message user">
            <div class="bubble">${escapeHtml(content)}</div>
            <div class="message-avatar">👤</div>
        </div>
    `;
    scrollToBottom(messagesDiv);

    // 同时在事件流中显示用户输入
    addEvent('status', '用户', '发送消息', content.length > 50 ? content.substring(0, 50) + '...' : content);
}

function addAIMessage(content, reasoning, toolCalls) {
    const messagesDiv = document.getElementById('chatMessages');

    // 渲染工具调用
    let toolCallsHtml = '';
    if (toolCalls && toolCalls.length > 0) {
        toolCallsHtml = '<div class="tool-calls">' + toolCalls.map(tc => {
            if (tc.result) {
                const shortResult = tc.result.length > 200
                    ? tc.result.substring(0, 200) + '...'
                    : tc.result;
                return `<div class="tool-call result">
                    <div class="tool-call-header">
                        <span class="tool-call-icon">📥</span>
                        <span class="tool-call-name">${escapeHtml(tc.name)}</span>
                        <span class="tool-call-label">返回结果</span>
                    </div>
                    <div class="tool-call-content">${escapeHtml(shortResult)}</div>
                </div>`;
            } else {
                return `<div class="tool-call invoke">
                    <div class="tool-call-header">
                        <span class="tool-call-icon">🔧</span>
                        <span class="tool-call-name">${escapeHtml(tc.name)}</span>
                        <span class="tool-call-label">调用</span>
                    </div>
                    <div class="tool-call-content">${escapeHtml(JSON.stringify(tc.args, null, 2))}</div>
                </div>`;
            }
        }).join('') + '</div>';
    }

    // 渲染推理过程
    let reasoningHtml = '';
    if (reasoning) {
        reasoningHtml = `
            <div class="reasoning">
                <div class="reasoning-header">
                    <span class="reasoning-icon">💭</span>
                    <span class="reasoning-title">思考过程</span>
                    <button class="reasoning-toggle" onclick="toggleReasoning(this)">展开</button>
                </div>
                <div class="reasoning-content" style="display: none;">
                    ${escapeHtml(reasoning)}
                </div>
            </div>
        `;
    }

    // 渲染主内容
    const formattedContent = formatMarkdown(content);

    messagesDiv.innerHTML += `
        <div class="message ai">
            <div class="message-avatar">🤖</div>
            <div class="bubble">
                ${toolCallsHtml}
                <div class="ai-content">${formattedContent}</div>
                ${reasoningHtml}
            </div>
        </div>
    `;
    scrollToBottom(messagesDiv);
}

function toggleReasoning(btn) {
    const content = btn.parentElement.nextElementSibling;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.textContent = '收起';
    } else {
        content.style.display = 'none';
        btn.textContent = '展开';
    }
}

function addSystemMessage(content) {
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML += `
        <div class="message system">
            <div class="bubble">${content}</div>
        </div>
    `;
    scrollToBottom(messagesDiv);
}

// ==================== 用户操作 ====================

function initAgent(apiKey, model) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const initBtn = document.getElementById('initBtn');
        initBtn.innerHTML = `
            <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
            </svg>
            <span>初始化中...</span>
        `;

        ws.send(JSON.stringify({
            action: 'init_agent',
            api_key: apiKey,
            model: model
        }));

        addEvent('processing', '系统', '正在初始化 Agent', `使用 ${model} 模型...`);
    } else {
        showNotification('未连接到服务器，请刷新页面重试', 'error');
    }
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message && ws && ws.readyState === WebSocket.OPEN && !isProcessing) {
        ws.send(JSON.stringify({ action: 'send_message', message: message }));
        input.value = '';
    }
}

function useSuggestion(text) {
    const input = document.getElementById('chatInput');
    input.value = text;
    input.focus();
}

function clearEvents() {
    const eventsList = document.getElementById('eventsList');
    eventsList.innerHTML = `
        <div class="event-welcome">
            <div class="event-welcome-icon">📡</div>
            <span>事件流已清空</span>
        </div>
    `;
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'clear' }));
    }
}

// ==================== 工具函数 ====================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';

    return escapeHtml(text)
        .replace(/^## (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h5>$1</h5>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/\n/g, '<br>');
}

function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

// ==================== 键盘快捷键 ====================

document.addEventListener('keydown', (e) => {
    // ESC 关闭弹窗
    if (e.key === 'Escape') {
        hideConfigModal();
        closeSkillModal();
    }

    // Ctrl+Enter 发送消息
    if (e.ctrlKey && e.key === 'Enter') {
        sendMessage();
    }
});

// ==================== 点击弹窗外部关闭 ====================

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        if (e.target.id === 'skillModal') {
            closeSkillModal();
        }
    }
});

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    connect();
});
