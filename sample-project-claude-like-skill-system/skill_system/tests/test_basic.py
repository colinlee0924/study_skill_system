"""
基础测试用例
"""

import pytest
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skill_system.core import SkillRegistry, SkillMetadata, BaseSkill
from skill_system.core.exceptions import SkillNotFoundError, SkillLoadError
from skill_system.config import SkillSystemConfig


class TestSkillRegistry:
    """测试 Skill Registry"""

    def test_registry_init(self):
        """测试 Registry 初始化"""
        registry = SkillRegistry()
        assert len(registry) == 0

    def test_register_skill(self):
        """测试注册 Skill"""
        registry = SkillRegistry()

        # 创建一个简单的测试 Skill
        class TestSkill(BaseSkill):
            @property
            def metadata(self):
                return SkillMetadata(
                    name="test_skill",
                    description="Test skill",
                    version="1.0.0"
                )

            def get_tools(self):
                return []

            def get_loader_tool(self):
                from langchain_core.tools import tool

                @tool
                def test_loader():
                    """Test loader"""
                    return "loaded"

                return test_loader

        skill = TestSkill()
        registry.register(skill)

        assert len(registry) == 1
        assert "test_skill" in registry

    def test_get_skill(self):
        """测试获取 Skill"""
        registry = SkillRegistry()

        class TestSkill(BaseSkill):
            @property
            def metadata(self):
                return SkillMetadata(
                    name="test_skill",
                    description="Test",
                    version="1.0.0"
                )

            def get_tools(self):
                return []

            def get_loader_tool(self):
                from langchain_core.tools import tool

                @tool
                def test_loader():
                    return "loaded"

                return test_loader

        skill = TestSkill()
        registry.register(skill)

        retrieved = registry.get("test_skill")
        assert retrieved.metadata.name == "test_skill"

    def test_get_nonexistent_skill(self):
        """测试获取不存在的 Skill"""
        registry = SkillRegistry()

        with pytest.raises(SkillNotFoundError):
            registry.get("nonexistent")

    def test_list_skills(self):
        """测试列出所有 Skills"""
        registry = SkillRegistry()

        class TestSkill1(BaseSkill):
            @property
            def metadata(self):
                return SkillMetadata(name="skill1", description="", version="1.0.0")

            def get_tools(self):
                return []

            def get_loader_tool(self):
                from langchain_core.tools import tool

                @tool
                def loader():
                    return "loaded"

                return loader

        class TestSkill2(BaseSkill):
            @property
            def metadata(self):
                return SkillMetadata(name="skill2", description="", version="1.0.0")

            def get_tools(self):
                return []

            def get_loader_tool(self):
                from langchain_core.tools import tool

                @tool
                def loader():
                    return "loaded"

                return loader

        registry.register(TestSkill1())
        registry.register(TestSkill2())

        skills = registry.list_skills()
        assert len(skills) == 2
        assert "skill1" in skills
        assert "skill2" in skills


class TestSkillSystemConfig:
    """测试配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SkillSystemConfig()

        assert config.state_mode == "replace"
        assert config.verbose is False
        assert config.auto_discover is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = SkillSystemConfig(
            skills_dir=Path("./custom_skills"),
            state_mode="fifo",
            max_concurrent_skills=5,
            verbose=True
        )

        assert config.skills_dir == Path("./custom_skills")
        assert config.state_mode == "fifo"
        assert config.max_concurrent_skills == 5
        assert config.verbose is True

    def test_invalid_state_mode(self):
        """测试无效的状态模式"""
        with pytest.raises(ValueError):
            SkillSystemConfig(state_mode="invalid_mode")

    def test_config_to_dict(self):
        """测试配置转字典"""
        config = SkillSystemConfig(
            skills_dir=Path("./skills"),
            state_mode="accumulate"
        )

        config_dict = config.to_dict()

        assert config_dict["state_mode"] == "accumulate"
        assert "skills_dir" in config_dict

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "skills_dir": "./skills",
            "state_mode": "fifo",
            "max_concurrent_skills": 3
        }

        config = SkillSystemConfig.from_dict(config_dict)

        assert config.state_mode == "fifo"
        assert config.max_concurrent_skills == 3


class TestSkillMetadata:
    """测试 Skill 元数据"""

    def test_metadata_creation(self):
        """测试元数据创建"""
        meta = SkillMetadata(
            name="test_skill",
            description="Test description",
            version="1.0.0",
            tags=["test", "example"],
            visibility="public"
        )

        assert meta.name == "test_skill"
        assert "test" in meta.tags
        assert meta.visibility == "public"

    def test_metadata_to_dict(self):
        """测试元数据转字典"""
        meta = SkillMetadata(
            name="test_skill",
            description="Test",
            version="1.0.0"
        )

        meta_dict = meta.to_dict()

        assert meta_dict["name"] == "test_skill"
        assert meta_dict["version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
