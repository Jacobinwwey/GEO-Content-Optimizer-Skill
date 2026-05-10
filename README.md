# GEO Content Optimizer Skill— AI 内容优化分析工具

基于 [Claude Code Skill](https://code.claude.com/docs/en/skills) 的 AI 网页内容优化分析工具。输入一个 URL，自动抓取页面、执行多角度 Google 搜索、获取 Google AI 概览（AI Overview），对比分析后生成可执行的内容优化建议报告。

> **GEO** = Generative Engine Optimization（生成式引擎优化），针对 Google AI Overview、Perplexity 等 AI 搜索场景优化网页内容。

> 零依赖：无需 Python 环境、无需 API Key。直接使用 Claude Code 内置工具（WebSearch、Web Reader、Playwright）完成所有操作。
 
---

## 工作原理

6 阶段自动化分析流水线：

```
URL → 抓取标题 → 查询扩展研究 → 提取主查询
                                    ↓
              优化报告 ← 对比分析 ← 获取 AI 概览 + 搜索摘要
```

| 阶段 | 说明 | 使用工具 |
|------|------|----------|
| 1. 抓取标题 | 访问页面，提取 H1/标题 | Web Reader |
| 2. 查询扩展 | 基于标题进行多角度 Google 搜索 | WebSearch |
| 3. 提取主查询 | 从搜索结果提炼核心 Google 搜索词 | Claude 推理 |
| 4. 获取 AI 概览 | 从 Google 搜索结果中获取 AI Overview | Playwright + WebSearch |
| 5. 搜索摘要 | 将搜索结果整理为结构化摘要 | Claude 推理 |
| 6. 对比分析 | 对比摘要与 AI 概览，生成优化报告 | Claude 推理 |

---

## 快速开始

### 前置条件

- 已安装 [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code),或者[codex]
- 已安装 [agent-browser](https://github.com/nicekid1/agent-browser)（推荐，轻量级浏览器自动化）：`npm i -g agent-browser && agent-browser install`
- 已配置 [Playwright MCP Server](https://github.com/anthropics/claude-code/tree/main/mcps/playwright)（可选，agent-browser 不可用时的兜底方案）

### 安装

```bash
git clone https://github.com/<your-username>/geo-ai-agent.git
cd geo-ai-agent
claude
```

Skill 会从 `.claude/skills/geo-content-optimizer/` 目录自动加载，无需额外配置。

### 使用

在 Claude Code 中输入斜杠命令：

```
/geo-content-optimizer https://example.com
```

也可以自然语言触发：

```
分析 https://example.com 的内容优化建议
```

---

## 输出文件

运行后自动生成到 `output/` 目录：

| 文件 | 说明 |
|------|------|
| `report.md` | 最终优化报告（含对比表格 + 行动建议） |
| `query_fanout.md` | 多角度搜索原始结果 |
| `ai_overview.md` | Google AI 概览内容 |
| `query_fanout_summary.md` | 搜索结果结构化摘要 |

### 报告内容

最终 `report.md` 包含：

- **对比表格** — 你的内容 vs Google AI 概览的多维度对比
- **模式分析** — 搜索生态中的共性与趋势
- **内容差距** — AI 概览覆盖但你的页面缺失的话题
- **行动建议** — 按优先级排列的具体优化措施

---

## 项目结构

```
geo-ai-agent/
├── .claude/
│   └── skills/
│       └── geo-content-optimizer/
│           ├── SKILL.md          # Skill 定义与工作流指令
│           └── README.md         # Skill 说明文档
├── output/                       # 分析报告输出（已 gitignore）
├── .gitignore
└── README.md                     # 本文件
```

---
 
 

## License

MIT
