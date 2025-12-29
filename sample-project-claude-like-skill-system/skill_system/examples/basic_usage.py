"""
基础使用示例

演示如何创建和使用 Skill Agent
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 專案根目錄 (skill_system_full 的上一層)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 加载环境变量 (從專案根目錄)
load_dotenv(PROJECT_ROOT / ".env")

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skill_system import create_skill_agent, SkillSystemConfig
from langchain_anthropic import ChatAnthropic


def example_basic():
    """基础示例：使用默认配置"""
    print("=" * 60)
    print("示例 1: 基础使用")
    print("=" * 60)

    # Skills 目錄
    skills_dir = Path(__file__).parent.parent / "skills"

    # 創建配置
    config = SkillSystemConfig(
        skills_dir=skills_dir,
        verbose=True
    )

    # 创建 Agent（使用 Claude）
    agent = create_skill_agent(
        model=ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0),
        config=config
    )

    print(f"Agent 创建成功！已加载 {len(agent.registry)} 个 Skills")
    print(f"可用 Skills: {agent.list_skills()}\n")

    # 测试对话
    messages = [
        {"role": "user", "content": "我需要处理一个 PDF 文件，请帮我加载相关能力"}
    ]

    print("用户: 我需要处理一个 PDF 文件，请帮我加载相关能力")
    print("\nAgent 执行中...\n")

    result = agent.invoke({"messages": messages})

    print("Agent 响应:")
    print(result["messages"][-1].content)


def example_with_config():
    """使用自定义配置"""
    print("\n" + "=" * 60)
    print("示例 2: 自定义配置")
    print("=" * 60)

    # 自定义配置
    config = SkillSystemConfig(
        skills_dir=Path(__file__).parent.parent / "skills",
        state_mode="fifo",
        max_concurrent_skills=2,
        verbose=True,
        log_level="DEBUG"
    )

    agent = create_skill_agent(
        model=ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0),
        config=config
    )

    print(f"\n已加载 Skills: {agent.list_skills()}")

    # 复杂任务
    messages = [
        {
            "role": "user",
            "content": "假设我有一个 report.pdf，请帮我：1. 转换成 CSV  2. 计算统计数据"
        }
    ]

    print("\n用户: 假设我有一个 report.pdf，请帮我：1. 转换成 CSV  2. 计算统计数据")
    print("\nAgent 执行中...\n")

    result = agent.invoke({"messages": messages})

    print("Agent 响应:")
    print(result["messages"][-1].content)


def example_search_skills():
    """搜索 Skills"""
    print("\n" + "=" * 60)
    print("示例 3: 搜索 Skills")
    print("=" * 60)

    agent = create_skill_agent(
        model=ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    )

    # 按标签搜索
    print("\n搜索标签包含 'pdf' 的 Skills:")
    pdf_skills = agent.search_skills(tags=["pdf"])
    for skill in pdf_skills:
        print(f"- {skill.name}: {skill.description}")

    # 按关键词搜索
    print("\n搜索关键词 'data' 的 Skills:")
    data_skills = agent.search_skills(query="data")
    for skill in data_skills:
        print(f"- {skill.name}: {skill.description}")


def example_skill_info():
    """获取 Skill 详细信息"""
    print("\n" + "=" * 60)
    print("示例 4: 获取 Skill 信息")
    print("=" * 60)

    agent = create_skill_agent(
        model=ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    )

    for skill_name in agent.list_skills():
        info = agent.get_skill_info(skill_name)
        print(f"\nSkill: {info.name}")
        print(f"  版本: {info.version}")
        print(f"  描述: {info.description}")
        print(f"  标签: {', '.join(info.tags)}")
        print(f"  可见性: {info.visibility}")
        print(f"  依赖: {', '.join(info.dependencies) if info.dependencies else '无'}")


if __name__ == "__main__":
    # 运行所有示例
    try:
        example_basic()
        # example_with_config()
        # example_search_skills()
        # example_skill_info()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
