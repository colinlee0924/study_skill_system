# -*- coding: utf-8 -*-
"""
Agent Factory - 使用 LangChain 1.0 create_agent 创建 Skill-aware Agent

核心变化：
- 使用 langchain.agents.create_agent 而非 langgraph.prebuilt.create_react_agent
- 使用 langchain.agents.middleware 实现动态工具过滤
- 支持自定义 state_schema 追踪 skills_loaded
"""

from typing import Optional, Callable, Any, Dict, List
from pathlib import Path
import logging

from langchain_core.language_models import BaseChatModel

# LangChain 1.0 正确的导入
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

from .core import SkillRegistry, SkillState, SkillMetadata
from .core.state import SkillStateAccumulative, SkillStateFIFO
from .middleware import SkillMiddleware
from .config import SkillSystemConfig, load_config
from .utils import setup_logger, generate_system_prompt

logger = logging.getLogger(__name__)


class SkillAgent:
    """
    Skill Agent 包装器

    封装了 Agent 和 Registry，提供便捷的管理接口
    """

    def __init__(
        self,
        agent: Any,
        registry: SkillRegistry,
        config: SkillSystemConfig
    ):
        """
        Args:
            agent: LangChain Agent 实例
            registry: Skill Registry
            config: 系统配置
        """
        self.agent = agent
        self.registry = registry
        self.config = config

    def invoke(self, input_data: Dict[str, Any], **kwargs) -> Any:
        """调用 Agent"""
        return self.agent.invoke(input_data, **kwargs)

    async def ainvoke(self, input_data: Dict[str, Any], **kwargs) -> Any:
        """异步调用 Agent"""
        return await self.agent.ainvoke(input_data, **kwargs)

    def stream(self, input_data: Dict[str, Any], **kwargs):
        """流式调用 Agent"""
        return self.agent.stream(input_data, **kwargs)

    async def astream(self, input_data: Dict[str, Any], **kwargs):
        """异步流式调用 Agent"""
        return self.agent.astream(input_data, **kwargs)

    def list_skills(self) -> List[str]:
        """列出所有已注册的 Skills"""
        return self.registry.list_skills()

    def get_skill_info(self, skill_name: str) -> SkillMetadata:
        """获取 Skill 信息"""
        return self.registry.get_metadata(skill_name)

    def search_skills(
        self,
        query: str = "",
        tags: Optional[List[str]] = None
    ) -> List[SkillMetadata]:
        """搜索 Skills"""
        return self.registry.search(query=query, tags=tags)

    def __repr__(self) -> str:
        return f"<SkillAgent: {len(self.registry)} skills loaded>"


def create_skill_agent(
    model: BaseChatModel,
    config: Optional[SkillSystemConfig] = None,
    config_path: Optional[Path] = None,
    custom_system_prompt: Optional[str] = None,
    filter_fn: Optional[Callable[[SkillMetadata], bool]] = None,
) -> SkillAgent:
    """
    创建 Skill-aware Agent（使用 LangChain 1.0 API）

    这是系统的主要入口函数，负责：
    1. 加载配置
    2. 初始化 Registry 并发现 Skills
    3. 配置 SkillMiddleware（动态工具过滤）
    4. 生成 System Prompt
    5. 创建 LangChain Agent
    6. 返回封装好的 SkillAgent

    Args:
        model: LangChain Chat Model (e.g., ChatOpenAI, ChatAnthropic, DeepSeekReasonerChatModel)
        config: SkillSystemConfig 实例（可选，会从 config_path 或默认值加载）
        config_path: 配置文件路径（可选）
        custom_system_prompt: 自定义 System Prompt（可选）
        filter_fn: 自定义 Skill 过滤函数（可选）

    Returns:
        SkillAgent 实例

    Example:
        ```python
        from langchain_openai import ChatOpenAI
        from skill_system import create_skill_agent, SkillSystemConfig

        # 方式 1：使用默认配置
        agent = create_skill_agent(model=ChatOpenAI(model="gpt-4"))

        # 方式 2：自定义配置
        config = SkillSystemConfig(
            skills_dir="./my_skills",
            state_mode="fifo",
            max_concurrent_skills=5,
            verbose=True
        )
        agent = create_skill_agent(model=ChatOpenAI(model="gpt-4"), config=config)

        # 使用
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Convert PDF to CSV"}]
        })
        ```
    """
    # 1. 加载配置
    if config is None:
        config = load_config(config_path)

    # 2. 设置日志
    if config.verbose:
        setup_logger(level=config.log_level)

    logger.info(f"Initializing Skill Agent with config: {config.to_dict()}")

    # 3. 初始化 Registry
    registry = SkillRegistry()

    # 4. 自动发现并加载 Skills
    if config.auto_discover and config.skills_dir.exists():
        logger.info(f"Auto-discovering skills from: {config.skills_dir}")
        loaded_count = registry.discover_and_load(
            skills_dir=config.skills_dir,
            module_name=config.skill_module_name
        )
        logger.info(f"Loaded {loaded_count} skills")
    else:
        logger.warning(f"Skills directory not found or auto-discover disabled: {config.skills_dir}")

    if len(registry) == 0:
        logger.warning("No skills loaded! Agent will have no skill capabilities.")

    # 5. 定义过滤函数（基于可见性）
    def visibility_filter(meta: SkillMetadata) -> bool:
        if not config.filter_by_visibility:
            return True
        return meta.visibility in config.allowed_visibilities

    # 组合用户自定义过滤函数
    combined_filter = filter_fn
    if filter_fn:
        combined_filter = lambda meta: visibility_filter(meta) and filter_fn(meta)
    else:
        combined_filter = visibility_filter

    # 6. 获取所有工具（用于注册到 Agent）
    all_tools = registry.get_all_tools(filter_fn=combined_filter)
    logger.info(f"Total tools registered: {len(all_tools)}")

    # 7. 选择状态管理模式
    if config.state_mode == "replace":
        state_schema = SkillState
    elif config.state_mode == "accumulate":
        state_schema = SkillStateAccumulative
    elif config.state_mode == "fifo":
        state_schema = SkillStateFIFO
    else:
        raise ValueError(f"Invalid state_mode: {config.state_mode}")

    logger.info(f"Using state mode: {config.state_mode}")

    # 8. 创建中间件列表
    middleware_list: List[AgentMiddleware] = []

    if config.middleware_enabled:
        # 【核心】创建 SkillMiddleware 实现动态工具过滤
        skill_middleware = SkillMiddleware(
            skill_registry=registry,
            verbose=config.verbose,
            filter_fn=combined_filter
        )
        middleware_list.append(skill_middleware)
        logger.info("SkillMiddleware enabled - dynamic tool filtering active")

    # 9. 生成 System Prompt
    available_skills = registry.list_skills(filter_fn=combined_filter)
    system_prompt = custom_system_prompt or generate_system_prompt(
        available_skill_names=available_skills,
        custom_instructions=""
    )

    logger.debug(f"System prompt:\n{system_prompt}")

    # 10. 创建 LangChain 1.0 Agent
    # 使用 langchain.agents.create_agent，支持 middleware 和 state_schema
    try:
        agent = create_agent(
            model=model,
            tools=all_tools,
            middleware=middleware_list if middleware_list else (),
            state_schema=state_schema,
            system_prompt=system_prompt,  # 正确的参数名
            debug=config.verbose
        )
        logger.info("Agent created with middleware and state_schema support")
    except TypeError as e:
        # 如果某些参数不支持，尝试简化版本
        logger.warning(f"Falling back to simplified agent creation: {e}")
        try:
            agent = create_agent(
                model=model,
                tools=all_tools,
                middleware=middleware_list if middleware_list else (),
                system_prompt=system_prompt,
            )
            logger.info("Agent created with middleware support (no state_schema)")
        except TypeError:
            # 最后回退
            agent = create_agent(
                model=model,
                tools=all_tools,
            )
            logger.warning("Agent created without middleware - dynamic filtering disabled!")

    logger.info("Skill Agent created successfully")

    # 11. 返回封装的 SkillAgent
    return SkillAgent(agent=agent, registry=registry, config=config)


def create_custom_agent(
    model: BaseChatModel,
    skills_dir: Path,
    state_mode: str = "replace",
    verbose: bool = False,
    **kwargs
) -> SkillAgent:
    """
    快捷函数：创建自定义配置的 Agent

    Args:
        model: Chat Model
        skills_dir: Skills 目录
        state_mode: 状态模式 (replace/accumulate/fifo)
        verbose: 详细日志
        **kwargs: 其他配置参数

    Returns:
        SkillAgent 实例
    """
    config = SkillSystemConfig(
        skills_dir=skills_dir,
        state_mode=state_mode,
        verbose=verbose,
        **kwargs
    )
    return create_skill_agent(model=model, config=config)
