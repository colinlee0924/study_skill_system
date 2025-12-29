# 快速开始指南

## 5 分钟上手 Skill System

### 1. 安装依赖

```bash
pip install langchain langgraph langchain-openai pdfplumber pandas numpy matplotlib
```

### 2. 设置环境变量

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. 运行第一个示例

```python
# my_first_agent.py
from skill_system import create_skill_agent
from langchain_openai import ChatOpenAI

# 创建 Agent
agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4", temperature=0)
)

# 使用 Agent
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "我有一个 PDF 文件需要处理，请帮我加载相关能力"
    }]
})

print(result["messages"][-1].content)
```

运行：
```bash
python my_first_agent.py
```

### 4. 理解发生了什么

```
1. Agent 初始状态：
   - 只能看到 skill_pdf_processing, skill_data_analysis loaders
   - 还没有实际的处理工具

2. Agent 识别需求：
   - 用户需要 PDF 处理
   - 决定调用 skill_pdf_processing()

3. Skill 激活：
   - Loader 返回使用说明
   - 状态更新: skills_loaded = ["pdf_processing"]

4. 中间件生效：
   - 检测到 pdf_processing 已加载
   - 注入 pdf_to_csv, extract_pdf_text 等工具

5. Agent 现在可以使用：
   - pdf_to_csv()
   - extract_pdf_text()
   - parse_pdf_tables()
```

### 5. 进阶：自定义配置

```python
from skill_system import create_skill_agent, SkillSystemConfig
from pathlib import Path

# 自定义配置
config = SkillSystemConfig(
    skills_dir=Path("./skills"),
    state_mode="fifo",  # 最多同时 3 个 Skill
    max_concurrent_skills=3,
    verbose=True  # 查看详细日志
)

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    config=config
)
```

### 6. 常见任务示例

#### 任务 1：PDF 转 CSV

```python
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "把 report.pdf 转换成 CSV 格式"
    }]
})
```

**Agent 会自动**：
1. 加载 pdf_processing Skill
2. 使用 pdf_to_csv 工具
3. 返回结果

#### 任务 2：数据分析

```python
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "计算这组数据的统计信息：[10, 20, 30, 40, 50]"
    }]
})
```

**Agent 会自动**：
1. 加载 data_analysis Skill
2. 使用 calculate_statistics 工具
3. 返回统计结果

#### 任务 3：组合任务

```python
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": """
        请帮我：
        1. 从 sales.pdf 提取数据
        2. 转换成 CSV
        3. 计算销售额的统计信息
        4. 生成趋势图
        """
    }]
})
```

**Agent 会自动**：
1. 加载 pdf_processing Skill
2. 提取和转换数据
3. 加载 data_analysis Skill
4. 计算统计并生成图表

### 7. 创建你的第一个 Skill

```bash
# 创建目录
mkdir -p skills/email_sender
cd skills/email_sender
```

创建 `skill.py`:

```python
from pathlib import Path
from typing import List
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from skill_system.core.base_skill import BaseSkill, SkillMetadata


class EmailSenderSkill(BaseSkill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="email_sender",
            description="发送电子邮件的能力",
            version="1.0.0",
            tags=["email", "communication"],
            visibility="public"
        )

    def get_loader_tool(self) -> BaseTool:
        skill_instance = self

        @tool
        def skill_email_sender(runtime) -> Command:
            """Load email sending capabilities."""
            instructions = "Email Skill activated. Use send_email tool."
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=instructions,
                        tool_call_id=runtime.tool_call_id
                    )],
                    "skills_loaded": ["email_sender"]
                }
            )
        return skill_email_sender

    def get_tools(self) -> List[BaseTool]:
        @tool
        def send_email(to: str, subject: str, body: str) -> str:
            """Send an email."""
            # 实现发送逻辑
            return f"Email sent to {to}"

        return [send_email]


def create_skill(skill_dir: Path) -> BaseSkill:
    return EmailSenderSkill(skill_dir)
```

使用你的 Skill：

```python
agent = create_skill_agent(model=ChatOpenAI(model="gpt-4"))

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "发送一封邮件给 user@example.com"
    }]
})
```

### 8. 调试技巧

#### 查看已加载的 Skills

```python
print("Available Skills:", agent.list_skills())
```

#### 查看 Skill 信息

```python
for skill_name in agent.list_skills():
    info = agent.get_skill_info(skill_name)
    print(f"{skill_name}: {info.description}")
```

#### 启用详细日志

```python
config = SkillSystemConfig(verbose=True, log_level="DEBUG")
agent = create_skill_agent(model=ChatOpenAI(model="gpt-4"), config=config)
```

#### 搜索 Skills

```python
# 按标签搜索
pdf_skills = agent.search_skills(tags=["pdf"])

# 按关键词搜索
data_skills = agent.search_skills(query="data")
```

### 9. 性能优化建议

1. **选择合适的状态模式**：
   - 简单任务 → `state_mode="replace"`
   - 复杂任务 → `state_mode="accumulate"`
   - 控制成本 → `state_mode="fifo"`

2. **控制 Skill 数量**：
   - FIFO 模式下设置 `max_concurrent_skills=3`

3. **使用缓存**：
   - 重复任务可以复用已加载的 Skill

4. **合理组织 Skills**：
   - 相关功能组合成一个 Skill
   - 避免过度拆分导致频繁切换

### 10. 常见问题

#### Q: 为什么 Agent 没有加载我的 Skill？

A: 检查：
1. Skill 目录是否在 `skills_dir` 下
2. `skill.py` 是否存在
3. `create_skill()` 函数是否正确定义
4. 运行时查看日志：`verbose=True`

#### Q: 如何禁用某个 Skill？

A: 在 SkillMetadata 中设置 `enabled=False`

#### Q: 中间件没有生效？

A: 检查：
1. `middleware_enabled=True`
2. 状态更新是否正确：`skills_loaded` 列表
3. Loader Tool 是否返回 `Command` 对象

#### Q: 如何限制用户权限？

A: 使用 `filter_fn` 参数：

```python
def my_filter(meta):
    # 只允许 public 的 Skill
    return meta.visibility == "public"

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    filter_fn=my_filter
)
```

### 11. 下一步

- 阅读完整文档：[README.md](./README.md)
- 查看更多示例：[examples/](./examples/)
- 创建自己的 Skills
- 贡献到社区

### 12. 获取帮助

- 问题反馈：GitHub Issues
- 文档：查看 README.md
- 示例代码：examples/ 目录

---

🎉 恭喜！你已经掌握了 Skill System 的基础用法！
