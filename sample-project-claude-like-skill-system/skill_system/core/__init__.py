"""
Claude-Style Skills System - Core Module
核心模块：定义基础类、接口和类型
"""

from .base_skill import BaseSkill, SkillMetadata
from .state import SkillState, skill_list_reducer, skill_list_accumulator, skill_list_fifo
from .registry import SkillRegistry
from .exceptions import SkillError, SkillNotFoundError, SkillLoadError

__all__ = [
    "BaseSkill",
    "SkillMetadata",
    "SkillState",
    "SkillRegistry",
    "skill_list_reducer",
    "skill_list_accumulator",
    "skill_list_fifo",
    "SkillError",
    "SkillNotFoundError",
    "SkillLoadError",
]
