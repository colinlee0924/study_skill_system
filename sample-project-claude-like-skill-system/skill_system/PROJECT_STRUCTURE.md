# 项目结构说明

## 📁 完整目录树

```
skill_system/
├── __init__.py                    # 主模块入口
├── agent_factory.py               # Agent 工厂函数
├── README.md                      # 项目文档
├── QUICKSTART.md                  # 快速开始指南
├── PROJECT_STRUCTURE.md           # 本文件
├── config.example.yaml            # 配置文件示例
│
├── core/                          # 核心组件
│   ├── __init__.py
│   ├── base_skill.py             # Skill 基类和元数据
│   ├── state.py                  # 状态管理（Replace/Accumulate/FIFO）
│   ├── registry.py               # Skill 注册中心
│   └── exceptions.py             # 自定义异常
│
├── middleware/                    # 中间件
│   ├── __init__.py
│   └── skill_middleware.py       # 运行时工具过滤中间件
│
├── skills/                        # Skills 库
│   ├── pdf_processing/           # PDF 处理 Skill
│   │   ├── skill.py              # Skill 实现
│   │   └── instructions.md       # 使用说明
│   └── data_analysis/            # 数据分析 Skill
│       ├── skill.py
│       └── instructions.md
│
├── config/                        # 配置管理
│   ├── __init__.py
│   └── settings.py               # 配置类和加载函数
│
├── utils/                         # 工具函数
│   ├── __init__.py
│   ├── logger.py                 # 日志工具
│   └── helpers.py                # 辅助函数
│
├── examples/                      # 示例代码
│   └── basic_usage.py            # 基础使用示例
│
└── tests/                         # 测试用例
    └── test_basic.py             # 基础测试
```

## 🔍 核心文件详解

### 1. `__init__.py` - 主模块入口

导出所有公共 API：
- `create_skill_agent()` - 创建 Skill Agent
- `SkillSystemConfig` - 配置类
- `BaseSkill` - Skill 基类
- `SkillRegistry` - 注册中心
- 等等...

**作用**：提供统一的导入接口

### 2. `agent_factory.py` - Agent 工厂

核心函数：
- `create_skill_agent()` - 主要创建函数
- `SkillAgent` - Agent 包装器类
- `create_custom_agent()` - 快捷创建函数

**作用**：负责初始化和组装整个系统

### 3. `core/base_skill.py` - Skill 基类

定义：
- `SkillMetadata` - 元数据数据类
- `BaseSkill` - 抽象基类

**作用**：规范 Skill 的结构和接口

### 4. `core/state.py` - 状态管理

提供：
- `SkillState` - 默认状态类（Replace 模式）
- `skill_list_reducer` - 替换模式 reducer
- `skill_list_accumulator` - 累积模式 reducer
- `skill_list_fifo()` - FIFO 模式工厂函数

**作用**：管理已加载的 Skills 列表

### 5. `core/registry.py` - Skill 注册中心

功能：
- 注册/注销 Skill
- 查询和搜索 Skill
- 自动发现和加载 Skill
- 提供工具列表

**作用**：Skill 的中央管理器

### 6. `core/exceptions.py` - 异常定义

定义：
- `SkillError` - 基础异常
- `SkillNotFoundError` - Skill 未找到
- `SkillLoadError` - 加载失败
- `SkillPermissionError` - 权限错误

**作用**：规范错误处理

### 7. `middleware/skill_middleware.py` - 中间件

类：
- `SkillMiddleware` - 主中间件类
- `PermissionAwareSkillMiddleware` - 带权限控制
- `RateLimitedSkillMiddleware` - 带速率限制

**作用**：运行时动态过滤工具列表

### 8. `config/settings.py` - 配置管理

提供：
- `SkillSystemConfig` - 配置类
- `load_config()` - 配置加载函数
- 支持 YAML 文件和环境变量

**作用**：统一管理系统配置

### 9. `utils/` - 工具模块

- `logger.py` - 日志配置
- `helpers.py` - 辅助函数
  - `generate_system_prompt()` - 生成提示词
  - `format_skill_list()` - 格式化输出
  - `validate_skill_structure()` - 验证 Skill

**作用**：提供通用工具函数

## 📦 Skill 结构

每个 Skill 目录包含：

```
skill_name/
├── skill.py              # 必需：Skill 实现
├── instructions.md       # 推荐：使用说明
└── config.yaml          # 可选：配置文件
```

### `skill.py` 必须包含：

1. **Skill 类**：继承自 `BaseSkill`
2. **metadata 属性**：返回 `SkillMetadata`
3. **get_loader_tool()**：返回 Loader Tool
4. **get_tools()**：返回实际工具列表
5. **create_skill()**：工厂函数

### 示例结构：

```python
class MySkill(BaseSkill):
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(name="my_skill", ...)

    def get_loader_tool(self) -> BaseTool:
        @tool
        def skill_my_skill(runtime) -> Command:
            ...
        return skill_my_skill

    def get_tools(self) -> List[BaseTool]:
        return [tool1, tool2, ...]

def create_skill(skill_dir: Path) -> BaseSkill:
    return MySkill(skill_dir)
```

## 🔄 数据流

### 1. 初始化流程

```
create_skill_agent()
    ↓
加载配置 (SkillSystemConfig)
    ↓
创建 Registry (SkillRegistry)
    ↓
自动发现 Skills (discover_and_load)
    ↓
注册所有工具 (get_all_tools)
    ↓
创建中间件 (SkillMiddleware)
    ↓
生成 System Prompt
    ↓
创建 LangGraph Agent
    ↓
返回 SkillAgent
```

### 2. 运行时流程

```
用户请求
    ↓
Agent 分析任务
    ↓
决定需要某个 Skill
    ↓
调用 skill_xxx() Loader
    ↓
Loader 更新状态: skills_loaded = [...]
    ↓
Loader 返回使用说明
    ↓
Agent 准备下次工具调用
    ↓
中间件拦截 (wrap_model_call)
    ↓
读取 skills_loaded 状态
    ↓
过滤工具列表 (get_tools_for_skills)
    ↓
替换 request.tools
    ↓
Agent 看到相关工具
    ↓
Agent 使用工具完成任务
```

## 🎯 设计模式

### 1. 工厂模式

- `create_skill_agent()` - Agent 工厂
- `create_skill()` - Skill 工厂

### 2. 注册表模式

- `SkillRegistry` - 管理所有 Skill

### 3. 中间件模式

- `SkillMiddleware` - 拦截和修改请求

### 4. 策略模式

- `skill_list_reducer` - 不同的状态更新策略

### 5. 模板方法模式

- `BaseSkill` - 定义 Skill 结构模板

## 🔧 扩展点

### 1. 添加新 Skill

在 `skills/` 目录创建新文件夹，实现 Skill 类。

### 2. 自定义中间件

继承 `SkillMiddleware` 并重写方法。

### 3. 自定义状态管理

创建新的 reducer 函数。

### 4. 自定义配置

扩展 `SkillSystemConfig` 类。

### 5. 添加过滤器

使用 `filter_fn` 参数。

## 📊 模块依赖关系

```
agent_factory
    ├── core.registry
    ├── core.state
    ├── middleware.skill_middleware
    ├── config.settings
    └── utils.helpers

core.registry
    └── core.base_skill

middleware.skill_middleware
    ├── core.registry
    └── core.state

skills/*
    └── core.base_skill
```

## 🧪 测试结构

```
tests/
├── test_basic.py           # 基础组件测试
├── test_registry.py        # Registry 测试（待添加）
├── test_middleware.py      # 中间件测试（待添加）
├── test_skills.py          # Skills 测试（待添加）
└── test_integration.py     # 集成测试（待添加）
```

## 📚 文档结构

```
README.md              # 完整文档
QUICKSTART.md          # 快速开始
PROJECT_STRUCTURE.md   # 本文件
config.example.yaml    # 配置示例
skills/*/instructions.md  # 各 Skill 使用说明
```

## 🚀 部署清单

生产环境部署需要：

1. ✅ 安装依赖
2. ✅ 配置环境变量（API Key 等）
3. ✅ 复制 config.example.yaml 为 config.yaml
4. ✅ 根据需求修改配置
5. ✅ 确保 skills/ 目录包含所需 Skills
6. ✅ 运行测试：`pytest tests/`
7. ✅ 启动应用

## 🔐 安全考虑

1. **API Key 管理**：使用环境变量
2. **权限控制**：使用 `filter_fn` 和 `visibility`
3. **输入验证**：在 Tool 中验证参数
4. **日志脱敏**：不记录敏感信息
5. **依赖安全**：定期更新依赖包

## 📝 开发规范

1. **代码风格**：遵循 PEP 8
2. **文档字符串**：使用 Google Style
3. **类型提示**：尽可能添加类型注解
4. **测试覆盖**：核心功能需要测试
5. **版本管理**：使用语义化版本号

---

**版本**：1.0.0
**最后更新**：2025-01-XX
**维护者**：MuyuCheney
