"""
辅助工具函数
"""

from typing import List, Dict, Any
from skill_system.core.base_skill import SkillMetadata


def format_skill_list(skills_metadata: List[SkillMetadata]) -> str:
    """
    格式化 Skill 列表为可读文本

    Args:
        skills_metadata: SkillMetadata 列表

    Returns:
        格式化后的文本
    """
    if not skills_metadata:
        return "No skills available."

    output = "Available Skills:\n\n"

    for i, meta in enumerate(skills_metadata, 1):
        output += f"{i}. **{meta.name}** (v{meta.version})\n"
        output += f"   Description: {meta.description}\n"
        output += f"   Tags: {', '.join(meta.tags)}\n"
        output += f"   Visibility: {meta.visibility}\n"
        if meta.dependencies:
            output += f"   Dependencies: {', '.join(meta.dependencies)}\n"
        output += "\n"

    return output


def generate_system_prompt(
    available_skill_names: List[str],
    custom_instructions: str = ""
) -> str:
    """
    生成 Agent 的 System Prompt

    Args:
        available_skill_names: 可用的 Skill 名称列表
        custom_instructions: 自定义指令

    Returns:
        完整的 System Prompt
    """
    skill_loaders = "\n".join([
        f"- skill_{name}: Load {name.replace('_', ' ')} capabilities"
        for name in available_skill_names
    ])

    prompt = f"""You are an AI assistant with modular skills.

**Important Operating Principle**:
You start with minimal capabilities. When you need specific functionality:
1. Identify which skill you need based on the task
2. Call the corresponding skill_* loader tool first
3. Wait for the skill to be activated (you'll receive instructions)
4. Then use the newly available tools to complete the task

**Available Skill Loaders**:
{skill_loaders}

**Workflow Example**:
User: "Convert report.pdf to CSV and analyze the data"
1. You think: I need PDF processing → Call skill_pdf_processing
2. PDF Skill activates → You receive pdf_to_csv, extract_pdf_text tools
3. You use pdf_to_csv to convert the file
4. You think: Now I need data analysis → Call skill_data_analysis
5. Data Analysis Skill activates → You receive calculate_statistics tools
6. You use calculate_statistics to analyze

**Key Rules**:
- ALWAYS load the skill BEFORE trying to use its tools
- Don't assume tools are available without loading the skill first
- If you're unsure which skill to use, describe what you need and load the most relevant one
- Skills persist across conversation turns once loaded

{custom_instructions}
"""

    return prompt


def create_skill_config_template() -> Dict[str, Any]:
    """
    创建 Skill 配置模板

    Returns:
        配置字典模板
    """
    return {
        "name": "my_skill",
        "description": "Skill description",
        "version": "1.0.0",
        "tags": ["tag1", "tag2"],
        "visibility": "public",
        "dependencies": [],
        "required_permissions": [],
        "author": "Your Name",
        "enabled": True
    }


def validate_skill_structure(skill_dir) -> List[str]:
    """
    验证 Skill 目录结构

    Args:
        skill_dir: Skill 目录路径

    Returns:
        问题列表（空列表表示通过验证）
    """
    from pathlib import Path

    issues = []
    skill_path = Path(skill_dir)

    if not skill_path.exists():
        issues.append(f"Directory does not exist: {skill_path}")
        return issues

    if not skill_path.is_dir():
        issues.append(f"Not a directory: {skill_path}")
        return issues

    # 检查必需文件
    required_files = ["skill.py"]
    for file_name in required_files:
        file_path = skill_path / file_name
        if not file_path.exists():
            issues.append(f"Missing required file: {file_name}")

    # 检查可选文件
    optional_files = ["instructions.md", "config.yaml"]
    for file_name in optional_files:
        file_path = skill_path / file_name
        if not file_path.exists():
            issues.append(f"Warning: Optional file not found: {file_name}")

    return issues


def print_registry_status(registry) -> str:
    """
    打印 Registry 状态信息

    Args:
        registry: SkillRegistry 实例

    Returns:
        状态文本
    """
    skill_names = registry.list_skills()

    if not skill_names:
        return "Registry is empty. No skills loaded."

    output = f"Skill Registry Status\n"
    output += f"=====================\n\n"
    output += f"Total Skills: {len(skill_names)}\n\n"

    for name in skill_names:
        meta = registry.get_metadata(name)
        output += f"- {name} (v{meta.version})\n"
        output += f"  Status: {'Enabled' if meta.enabled else 'Disabled'}\n"
        output += f"  Visibility: {meta.visibility}\n"
        output += f"  Tools: {len(registry.get(name).get_tools())}\n"
        output += "\n"

    return output
