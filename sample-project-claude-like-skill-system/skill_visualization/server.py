# -*- coding: utf-8 -*-
"""
Claude Skills 可视化服务器 (FastAPI)

实时展示动态工具过滤的工作过程

运行: python skill_visualization/server.py
访问: http://localhost:10011
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv(override=True)

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn


# ==================== 全局状态 ====================

class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent = None
        self.is_processing = False
        self.skills_info: Dict[str, Any] = {}  # 存储 skill 详情

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# ==================== 自定义日志处理器 ====================

class WebSocketLogHandler(logging.Handler):
    """捕获 middleware 日志并广播到前端"""
    def __init__(self, conn_manager: ConnectionManager):
        super().__init__()
        self.manager = conn_manager
        self.loop = None

    def emit(self, record):
        try:
            msg = self.format(record)
            event = {
                "type": "log",
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": msg
            }

            # 特殊处理 middleware 日志
            if "SkillMiddleware" in msg:
                if "Skills loaded:" in msg:
                    skills = msg.split("Skills loaded:")[1].strip()
                    event["type"] = "middleware_filter"
                    event["skills_loaded"] = skills
                elif "Filtered tools" in msg:
                    tools_part = msg.split("Filtered tools")[1]
                    event["type"] = "middleware_filter"
                    event["filtered_tools"] = tools_part

            # 异步广播
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.manager.broadcast(event),
                    self.loop
                )
        except Exception:
            pass


# 设置日志处理器
log_handler = WebSocketLogHandler(manager)
log_handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
logging.getLogger('skill_system').addHandler(log_handler)
logging.getLogger('skill_system').setLevel(logging.INFO)


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    log_handler.loop = asyncio.get_event_loop()
    print("\n" + "=" * 60)
    print("  Claude Skills 可视化服务器")
    print("=" * 60)
    print(f"\n  访问地址: http://localhost:10011")
    print("\n  功能说明:")
    print("    1. 首次加载配置 API 密钥")
    print("    2. 点击技能查看使用说明")
    print("    3. 用户友好的事件解释")
    print("    4. 科技感现代 UI")
    print("\n" + "=" * 60 + "\n")
    yield
    print("\n服务器已停止")


app = FastAPI(title="Claude Skills Visualization", lifespan=lifespan)

# 挂载静态文件
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==================== API 路由 ====================

@app.get("/")
async def index():
    """返回主页面"""
    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await manager.connect(websocket)

    # 发送初始状态
    await websocket.send_json({
        "type": "init",
        "timestamp": datetime.now().isoformat(),
        "message": "连接成功",
        "agent_ready": manager.agent is not None
    })

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("action") == "init_agent":
                api_key = data.get("api_key")
                model = data.get("model", "deepseek-reasoner")
                await handle_init_agent(websocket, api_key, model)

            elif data.get("action") == "send_message":
                await handle_send_message(websocket, data.get("message", ""))

            elif data.get("action") == "get_skill_info":
                skill_name = data.get("skill_name")
                await handle_get_skill_info(websocket, skill_name)

            elif data.get("action") == "clear":
                await websocket.send_json({"type": "cleared"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def load_skills_info() -> Dict[str, Any]:
    """加载所有 skills 的详细信息（从 Python 文件读取）"""
    skills_info = {}
    skills_dir = PROJECT_ROOT / "skill_system" / "skills"

    if not skills_dir.exists():
        return skills_info

    # 遍历每个技能目录
    for skill_folder in skills_dir.iterdir():
        if not skill_folder.is_dir() or skill_folder.name.startswith('_'):
            continue

        skill_py = skill_folder / "skill.py"
        instructions_md = skill_folder / "instructions.md"

        if not skill_py.exists():
            continue

        try:
            # 动态导入技能模块
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_folder.name}",
                skill_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 创建技能实例获取元数据
            if hasattr(module, 'create_skill'):
                skill_instance = module.create_skill(skill_folder)
                metadata = skill_instance.metadata

                # 获取工具列表
                tools = skill_instance.get_tools()
                tool_list = []
                for tool in tools:
                    tool_info = {
                        'name': tool.name,
                        'description': tool.description or ''
                    }
                    tool_list.append(tool_info)

                # 读取 instructions
                instructions = ''
                if instructions_md.exists():
                    with open(instructions_md, 'r', encoding='utf-8') as f:
                        instructions = f.read()

                skills_info[metadata.name] = {
                    'name': metadata.name,
                    'description': metadata.description,
                    'instructions': instructions,
                    'tools': tool_list,
                    'version': metadata.version,
                    'tags': metadata.tags,
                    'author': metadata.author
                }

        except Exception as e:
            print(f"Error loading skill {skill_folder.name}: {e}")
            import traceback
            traceback.print_exc()

    return skills_info


async def handle_init_agent(websocket: WebSocket, api_key: str = None, model: str = "deepseek-reasoner"):
    """初始化 Agent"""
    await websocket.send_json({
        "type": "status",
        "status": "initializing",
        "message": "正在初始化 Agent..."
    })

    try:
        from skill_system import create_skill_agent, SkillSystemConfig, DeepSeekReasonerChatModel

        # 优先使用传入的 API key，否则使用环境变量
        final_api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not final_api_key:
            raise ValueError("未提供 API 密钥")

        # 根据模型选择创建对应的模型实例
        if model == "deepseek-chat":
            from skill_system import DeepSeekChatModel
            model_instance = DeepSeekChatModel(
                api_key=final_api_key,
                model_name="deepseek-chat",
                temperature=0.7
            )
        else:
            model_instance = DeepSeekReasonerChatModel(
                api_key=final_api_key,
                model_name="deepseek-reasoner",
                temperature=0.7
            )

        config = SkillSystemConfig(
            skills_dir=PROJECT_ROOT / "skill_system" / "skills",
            state_mode="replace",
            verbose=True,
            middleware_enabled=True
        )

        manager.agent = create_skill_agent(model=model_instance, config=config)
        skills = manager.agent.list_skills()

        # 加载 skills 详细信息
        manager.skills_info = load_skills_info()

        await manager.broadcast({
            "type": "agent_ready",
            "skills": skills,
            "skills_info": manager.skills_info,
            "total_tools": 9,
            "model": model,
            "message": f"Agent 初始化成功！已加载 {len(skills)} 个技能"
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"初始化失败: {str(e)}"
        })


async def handle_get_skill_info(websocket: WebSocket, skill_name: str):
    """返回指定 skill 的详细信息"""
    if skill_name in manager.skills_info:
        await websocket.send_json({
            "type": "skill_info",
            "skill": manager.skills_info[skill_name]
        })
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"未找到技能 '{skill_name}'"
        })


async def handle_send_message(websocket: WebSocket, user_message: str):
    """处理用户消息"""
    if not manager.agent:
        await websocket.send_json({
            "type": "error",
            "message": "Agent 未初始化，请先配置 API 设置"
        })
        return

    if manager.is_processing:
        await websocket.send_json({
            "type": "error",
            "message": "正在处理中，请稍候..."
        })
        return

    manager.is_processing = True

    try:
        # 广播用户消息
        await manager.broadcast({
            "type": "user_message",
            "timestamp": datetime.now().isoformat(),
            "content": user_message
        })

        # 广播处理开始
        await manager.broadcast({
            "type": "processing_start",
            "timestamp": datetime.now().isoformat()
        })

        # 在线程池中执行 Agent 调用
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: manager.agent.invoke({
                "messages": [{"role": "user", "content": user_message}]
            })
        )

        # 解析结果
        skills_loaded = result.get("skills_loaded", [])
        tool_calls = []
        ai_response = ""
        reasoning = ""

        for msg in result.get("messages", []):
            msg_type = msg.__class__.__name__

            if msg_type == "AIMessage":
                if msg.content:
                    ai_response = msg.content

                if hasattr(msg, "additional_kwargs"):
                    reasoning = msg.additional_kwargs.get("reasoning_content", "")

                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get("name") if isinstance(tc, dict) else tc.name
                        tool_args = tc.get("args") if isinstance(tc, dict) else tc.args
                        tool_calls.append({
                            "name": tool_name,
                            "args": tool_args
                        })

            elif msg_type == "ToolMessage":
                tool_calls.append({
                    "name": msg.name if hasattr(msg, "name") else "unknown",
                    "result": msg.content[:500] if len(msg.content) > 500 else msg.content
                })

        # 广播结果
        await manager.broadcast({
            "type": "ai_response",
            "timestamp": datetime.now().isoformat(),
            "content": ai_response,
            "reasoning": reasoning[:800] if reasoning else "",
            "skills_loaded": skills_loaded,
            "tool_calls": tool_calls
        })

        await manager.broadcast({
            "type": "processing_end",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        await manager.broadcast({
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"处理失败: {str(e)}"
        })
    finally:
        manager.is_processing = False


# ==================== 主入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=10011,
        reload=False,
        log_level="warning"
    )
