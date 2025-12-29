# Claude-Style Skills System for LangChain

一个模块化、可扩展的 Skill 管理系统，为 LangChain/LangGraph 实现类似 Claude Skills 的动态工具加载机制。

## ✨ 核心特性

- 🔄 **动态 Skill 加载**：运行时按需激活能力，减少 token 消耗
- 🎯 **智能工具过滤**：中间件自动过滤无关工具，降低认知负荷
- 📦 **模块化设计**：每个 Skill 独立封装，易于开发和维护
- ⚙️ **灵活状态管理**：支持 Replace/Accumulate/FIFO 三种模式
- 🔐 **权限控制**：基于可见性和权限的访问控制
- 🚀 **高性能**：减少延迟和错误率，提升 Agent 决策质量

## 📦 安装

```bash
# 克隆仓库
cd skill_system

# 安装依赖
pip install langchain langgraph langchain-openai pdfplumber pandas numpy matplotlib
```

## 🚀 快速开始

### 基础用法

```python
from skill_system import create_skill_agent, SkillSystemConfig
from langchain_openai import ChatOpenAI

# 创建 Agent
agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4")
)

# 使用
result = agent.invoke({
    "messages": [{"role": "user", "content": "帮我处理 PDF 文件"}]
})

print(result["messages"][-1].content)
```

### 自定义配置

```python
# 创建自定义配置
config = SkillSystemConfig(
    skills_dir="./my_skills",
    state_mode="fifo",           # 最多同时加载 N 个 Skill
    max_concurrent_skills=3,     # FIFO 模式下的限制
    verbose=True,                # 启用详细日志
    log_level="DEBUG"
)

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    config=config
)
```

## 📂 项目结构

```
skill_system/
├── core/                      # 核心组件
│   ├── base_skill.py         # Skill 基类和元数据
│   ├── state.py              # 状态管理
│   ├── registry.py           # Skill 注册中心
│   └── exceptions.py         # 异常定义
├── middleware/               # 中间件
│   └── skill_middleware.py  # 动态工具过滤
├── skills/                   # Skills 库
│   ├── pdf_processing/      # PDF 处理 Skill
│   │   ├── skill.py
│   │   └── instructions.md
│   └── data_analysis/       # 数据分析 Skill
│       ├── skill.py
│       └── instructions.md
├── config/                   # 配置管理
│   └── settings.py
├── utils/                    # 工具函数
│   ├── logger.py
│   └── helpers.py
├── examples/                 # 示例代码
│   └── basic_usage.py
├── tests/                    # 测试用例
├── agent_factory.py          # Agent 工厂
└── __init__.py
```

## 🎯 工作原理

### 1. 传统方式 vs Skills 方式

**传统方式（静态加载所有工具）：**
```
Agent 启动 → 注册 50 个工具 → 每次调用都看到所有 50 个工具
问题：高 token 消耗、高延迟、高错误率
```

**Skills 方式（动态加载）：**
```
Agent 启动 → 注册所有工具 → 中间件过滤 → Agent 只看到 Loaders
需要能力 → 调用 Loader → 更新状态 → 中间件注入对应工具
结果：低 token 消耗、低延迟、低错误率
```

### 2. 核心组件交互

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 请求
       ▼
┌─────────────────────────────────────┐
│          Skill Agent                │
│  ┌──────────────────────────────┐  │
│  │   LangGraph Agent            │  │
│  │  • System Prompt             │  │
│  │  • 注册所有工具              │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │   Skill Middleware           │  │
│  │  • 读取 skills_loaded 状态  │  │
│  │  • 动态过滤工具列表          │  │
│  │  • 只显示相关工具            │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │   Skill Registry             │  │
│  │  • 管理所有 Skills           │  │
│  │  • 提供工具查询              │  │
│  │  • 自动发现和加载            │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 3. 执行流程

```
1. User: "帮我处理 PDF 并分析数据"

2. Agent 初始状态:
   - skills_loaded: []
   - 可见工具: [skill_pdf_processing, skill_data_analysis]

3. Agent 决策: "需要 PDF 处理能力"
   → 调用 skill_pdf_processing()

4. Loader 更新状态:
   - skills_loaded: ["pdf_processing"]
   - 返回使用说明

5. 中间件拦截下次调用:
   - 检测到 skills_loaded = ["pdf_processing"]
   - 注入 pdf_to_csv, extract_pdf_text 等工具

6. Agent 使用工具:
   → pdf_to_csv("report.pdf")

7. Agent 决策: "需要数据分析能力"
   → 调用 skill_data_analysis()

8. 重复流程...
```

## 📝 创建自定义 Skill

### 1. 创建 Skill 目录

```bash
mkdir -p skills/my_skill
cd skills/my_skill
```

### 2. 编写 Skill 类 (skill.py)

```python
from pathlib import Path
from typing import List
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from skill_system.core.base_skill import BaseSkill, SkillMetadata


class MySkill(BaseSkill):
    """我的自定义 Skill"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="my_skill",
            description="我的 Skill 功能描述",
            version="1.0.0",
            tags=["custom", "example"],
            visibility="public",
            dependencies=["some_library"],
            author="Your Name"
        )

    def get_loader_tool(self) -> BaseTool:
        """Loader Tool"""
        skill_instance = self

        @tool
        def skill_my_skill(runtime) -> Command:
            """Load my custom skill capabilities."""
            instructions = skill_instance.get_instructions()
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=instructions,
                        tool_call_id=runtime.tool_call_id
                    )],
                    "skills_loaded": ["my_skill"]
                }
            )

        return skill_my_skill

    def get_tools(self) -> List[BaseTool]:
        """实际工具"""
        @tool
        def my_custom_tool(input_text: str) -> str:
            """My custom tool description"""
            # 实现你的功能
            return f"Processed: {input_text}"

        return [my_custom_tool]


def create_skill(skill_dir: Path) -> BaseSkill:
    """工厂函数"""
    return MySkill(skill_dir)
```

### 3. 编写使用说明 (instructions.md)

```markdown
# My Skill

自定义 Skill 已激活！

## 可用工具

### my_custom_tool
工具功能描述

**参数**：
- `input_text`: 输入文本

**示例**：
\```python
my_custom_tool(input_text="hello")
\```
```

### 4. 使用你的 Skill

```python
from skill_system import create_skill_agent
from langchain_openai import ChatOpenAI

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4")
)

# Agent 会自动发现并加载你的 Skill
result = agent.invoke({
    "messages": [{"role": "user", "content": "使用我的自定义功能"}]
})
```

## 🔧 配置选项

### SkillSystemConfig 完整参数

```python
config = SkillSystemConfig(
    # 基础配置
    skills_dir=Path("./skills"),          # Skills 目录

    # 状态管理
    state_mode="replace",                 # replace/accumulate/fifo
    max_concurrent_skills=3,              # FIFO 模式限制

    # 日志
    verbose=False,
    log_level="INFO",

    # Agent
    default_model="gpt-4",
    temperature=0.7,
    max_tokens=None,

    # 中间件
    middleware_enabled=True,

    # 自动发现
    auto_discover=True,
    skill_module_name="skill",            # skill.py

    # 过滤
    filter_by_visibility=True,
    allowed_visibilities=["public"],      # public/internal/private

    # 权限
    user_permissions=[],

    # 自定义
    custom_config={}
)
```

## 📊 性能优势

基于原文的测试结果：

| 指标 | 传统方式 (50 工具) | Skills 方式 (5-10 工具) |
|-----|------------------|---------------------|
| Token 消耗 | 高 | **降低 60-80%** |
| 延迟 | 高 | **降低 40-60%** |
| 错误率 | 高 | **降低 50%+** |
| 工具选择准确性 | 中 | **高** |

## 🎓 最佳实践

### 1. Skill 设计原则

- **单一职责**：每个 Skill 专注一个领域
- **独立性**：Skill 之间应该解耦
- **清晰命名**：Skill 名称应描述性强
- **完善文档**：提供详细的 instructions.md

### 2. System Prompt 优化

```python
custom_prompt = """
你是一个专业的 AI 助手。

重要规则：
1. 在使用工具前，先检查是否需要加载对应的 Skill
2. 如果需要 PDF 处理，先调用 skill_pdf_processing
3. 如果需要数据分析，先调用 skill_data_analysis
4. Skill 一旦加载，工具即可使用

工作流程：
分析任务 → 识别所需 Skill → 加载 Skill → 使用工具 → 完成任务
"""

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    custom_system_prompt=custom_prompt
)
```

### 3. 状态模式选择

- **Replace 模式**：简单任务，每次只需一个 Skill
- **Accumulate 模式**：复杂任务，需要多个 Skill 协作
- **FIFO 模式**：控制成本，限制同时加载数量

### 4. 错误处理

```python
from skill_system.core.exceptions import SkillNotFoundError, SkillLoadError

try:
    agent = create_skill_agent(model=ChatOpenAI(model="gpt-4"))
except SkillLoadError as e:
    print(f"Skill 加载失败: {e.skill_name} - {e.reason}")
except Exception as e:
    print(f"创建 Agent 失败: {e}")
```

## 📚 示例

查看 [examples/](./examples/) 目录获取更多示例：

- `basic_usage.py` - 基础使用
- (待添加) `custom_skill.py` - 创建自定义 Skill
- (待添加) `advanced_config.py` - 高级配置
- (待添加) `async_usage.py` - 异步使用

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 运行示例
python examples/basic_usage.py
```

## 🤝 贡献

欢迎贡献新的 Skills 或改进核心功能！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingSkill`)
3. 提交更改 (`git commit -m 'Add AmazingSkill'`)
4. 推送到分支 (`git push origin feature/AmazingSkill`)
5. 创建 Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

本项目灵感来自：
- [Anthropic Claude Skills](https://claude.com/blog/skills)
- [Building Claude-Style Skills in LangChain v1](https://www.linkedin.com/pulse/building-claude-style-skills-langchain-v1-batiste-roger-e5pdf)

## 📧 联系

- 作者：MuyuCheney
- 项目：[GitHub Repository](https://github.com/your-repo)
- 问题反馈：[Issues](https://github.com/your-repo/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
