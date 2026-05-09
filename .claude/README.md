# Claude Code 项目配置

## 目录结构

```
.claude/
├── commands/           # Skills (斜杠命令)
│   └── generate-diagrams.md
├── prompts/            # 提示词模板
│   └── diagram-prompts.md
└── memory/             # 持久化记忆
    └── (自动生成)
```

## 使用方法

### Skill 使用

在 Claude Code 中直接输入斜杠命令：

```bash
# 生成所有图表
/generate-diagrams

# 只生成ER图和数据流图
/generate-diagrams --type er,dataflow

# 指定输出目录
/generate-diagrams --output-dir ./docs/diagrams

# 生成详细版本
/generate-diagrams --style detailed
```

### 提示词模板使用

1. 打开 `prompts/diagram-prompts.md`
2. 复制需要的提示词模板
3. 粘贴到 Claude Code 中执行
4. 根据项目需求修改模板内容

## 可用 Skills

| Skill | 说明 | 用法 |
|-------|------|------|
| generate-diagrams | 生成项目文档图表 | `/generate-diagrams [options]` |

## 图表类型说明

### 数据流图 (Data Flow Diagram)
- 展示系统中的数据流动
- 包含顶层数据流图和详细数据流图
- 使用 Mermaid flowchart 语法

### 数据库ER图 (ER Diagram)
- 展示数据库实体及关系
- 包含完整版和简化版
- 使用 Mermaid erDiagram 语法

### 功能模块图 (Functional Module Diagram)
- 展示系统功能模块结构
- 分用户端和管理员端
- 使用 Mermaid mindmap 语法

### 用例图 (Use Case Diagram)
- 展示系统用例和参与者
- 包含用例规格说明表
- 使用 Mermaid flowchart 语法

## 图表查看

生成的 Markdown 文件包含 Mermaid 代码，可通过以下方式查看：

1. **VS Code**: 安装 Mermaid 插件
2. **Typora**: 原生支持 Mermaid
3. **GitHub/GitLab**: 直接渲染
4. **在线工具**: [Mermaid Live Editor](https://mermaid.live/)

## 自定义配置

### 修改输出目录

编辑 `commands/generate-diagrams.md`，修改默认输出目录：
```
--output-dir <path>: Output directory (default: `$HOME/Desktop/项目图表`)
```

### 添加新图表类型

在 `commands/generate-diagrams.md` 中添加新的图表类型说明。

### 自定义提示词

在 `prompts/diagram-prompts.md` 中添加项目特定的提示词模板。
