"""
Claude-Style Skills System for LangChain/LangGraph

一个模块化、可扩展的 Skill 管理系统，实现类似 Claude Skills 的动态工具加载机制。

主要特性：
- 动态 Skill 加载和卸载
- 运行时工具过滤（中间件）
- 模块化 Skill 设计
- 灵活的状态管理（Replace/Accumulate/FIFO）
- 权限和可见性控制

快速开始：
```python
from skill_system import create_skill_agent, SkillSystemConfig
from langchain_openai import ChatOpenAI

# 创建配置
config = SkillSystemConfig(
    skills_dir="./skills",
    state_mode="fifo",
    max_concurrent_skills=3
)

# 创建 Agent
agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    config=config
)

# 使用
result = agent.invoke({"messages": [{"role": "user", "content": "你的任务"}]})
```
"""

from .core import (
    BaseSkill,
    SkillMetadata,
    SkillState,
    SkillRegistry,
    skill_list_reducer,
    skill_list_accumulator,
    skill_list_fifo,
)
from .middleware import SkillMiddleware
from .config import SkillSystemConfig, load_config
from .agent_factory import create_skill_agent, SkillAgent
from .utils import setup_logger, get_logger

# 自定义模型支持
try:
    from .models import DeepSeekReasonerChatModel
except ImportError:
    DeepSeekReasonerChatModel = None

__version__ = "1.0.0"
__author__ = "MuyuCheney"

__all__ = [
    # Core
    "BaseSkill",
    "SkillMetadata",
    "SkillState",
    "SkillRegistry",
    "skill_list_reducer",
    "skill_list_accumulator",
    "skill_list_fifo",
    # Middleware
    "SkillMiddleware",
    # Config
    "SkillSystemConfig",
    "load_config",
    # Agent
    "create_skill_agent",
    "SkillAgent",
    # Utils
    "setup_logger",
    "get_logger",
    # Models
    "DeepSeekReasonerChatModel",
]
