"""
简化版 Skill Middleware

注意：由于当前 LangGraph 版本可能没有完整的中间件 API，
这里提供一个简化的实现方案。

实际应用中，可以通过以下方式实现动态工具过滤：
1. 使用自定义的 agent 图
2. 在工具调用前的节点中过滤工具
3. 通过状态管理控制可见工具
"""

import logging
from typing import List, Optional, Callable
from langchain_core.tools import BaseTool

from skill_system.core.state import SkillState
from skill_system.core.registry import SkillRegistry

logger = logging.getLogger(__name__)


class SimpleSkillMiddleware:
    """
    简化的 Skill 中间件

    提供核心功能：根据 skills_loaded 状态获取相关工具
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        verbose: bool = False,
        filter_fn: Optional[Callable] = None
    ):
        self.registry = skill_registry
        self.verbose = verbose
        self.filter_fn = filter_fn

    def get_tools_for_state(self, skills_loaded: List[str]) -> List[BaseTool]:
        """
        根据已加载的 Skills 获取工具

        Args:
            skills_loaded: 已加载的 Skill 名称列表

        Returns:
            过滤后的工具列表
        """
        tools = self.registry.get_tools_for_skills(skills_loaded)

        if self.filter_fn:
            tools = [t for t in tools if self.filter_fn(t)]

        if self.verbose:
            logger.info(f"Skills loaded: {skills_loaded}")
            logger.info(f"Available tools: {[t.name for t in tools]}")

        return tools


def create_skill_aware_tools(
    registry: SkillRegistry,
    skills_loaded: Optional[List[str]] = None
) -> List[BaseTool]:
    """
    便捷函数：根据状态创建工具列表

    Args:
        registry: Skill 注册中心
        skills_loaded: 已加载的 Skills（None 表示只返回 loaders）

    Returns:
        工具列表
    """
    if skills_loaded is None:
        skills_loaded = []

    return registry.get_tools_for_skills(skills_loaded)


# 为了向后兼容，提供一个占位符类
class SkillMiddleware:
    """
    Skill Middleware 占位符

    注意：完整的中间件功能需要 LangGraph 支持。
    当前版本提供简化实现。

    使用方法：
    ```python
    # 方法 1：手动管理工具列表
    middleware = SkillMiddleware(registry)
    tools = middleware.get_tools_for_skills(["pdf_processing"])

    # 方法 2：在 Agent 创建时注册所有工具
    all_tools = registry.get_all_tools()
    agent = create_react_agent(model, all_tools)
    ```
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        verbose: bool = False,
        filter_fn: Optional[Callable] = None
    ):
        self.registry = skill_registry
        self.verbose = verbose
        self.filter_fn = filter_fn
        logger.warning(
            "SkillMiddleware: 使用简化实现。"
            "完整的运行时工具过滤需要 LangGraph 中间件支持。"
        )

    def get_tools_for_skills(self, skills_loaded: List[str]) -> List[BaseTool]:
        """获取工具列表"""
        tools = self.registry.get_tools_for_skills(skills_loaded)

        if self.filter_fn:
            tools = [t for t in tools if self.filter_fn(t)]

        if self.verbose:
            logger.info(f"Skills loaded: {skills_loaded}")
            logger.info(f"Available tools: {[t.name for t in tools]}")

        return tools
