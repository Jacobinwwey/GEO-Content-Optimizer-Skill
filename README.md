<div align="center">

# GEO Toolkit for Claude Code

**AI 搜索优化技能包 — 让你的品牌内容被 ChatGPT、Perplexity、Gemini 引用**

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue)](https://claude.ai/code) [![Python 3.7+](https://img.shields.io/badge/Python-3.7%2B-green)](https://www.python.org/) [![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## 这是什么

GEO（Generative Engine Optimization）是面向 AI 搜索引擎的内容优化方法论。就像 SEO 优化 Google 排名，GEO 优化你的内容在 ChatGPT、Perplexity、Gemini、Google AI Overview 等 AI 引擎中的引用率。

本项目提供两个 Claude Code Skill，覆盖 GEO 全流程：

| Skill | 定位 | 核心能力 |
|-------|------|---------|
| **geo-optimizer** | 全流程中枢 | Schema 生成、可读性检测、集群规划、可见度监控 |
| **geo-content-optimizer** | 内容差距分析 | URL 分析、Google AI Overview 对比、优化建议 |

## 为什么需要 GEO

- **BrightEdge** 分析了 100 万条 AI 回答：68% 的引用来自高权威站点，43% 来自带 Schema 标记的 FAQ
- **McKinsey** 预测到 2026 年 40% 的搜索将通过 AI 完成
- 不做 GEO，等于在 AI 时代"不存在"

## 快速开始

### 安装

**方式一：使用 .skill 文件（推荐）**

将 `geo-optimizer.skill` 下载后放入 Claude Code 的 skills 目录：

```bash
# macOS / Linux
cp geo-optimizer.skill ~/.claude/skills/

# Windows
copy geo-optimizer.skill %USERPROFILE%\.claude\skills\
```

**方式二：克隆仓库**

```bash
git clone https://github.com/your-username/geo-start.git
cd geo-start
# skills 已在 .claude/skills/ 中就绪
```

### 前置要求

- [Claude Code](https://claude.ai/code) 已安装并登录
- Python 3.7+（用于运行辅助脚本）
- 可见度测试支持双引擎：[Kimi (Moonshot) API Key](https://platform.moonshot.cn/)（默认，国内直连）或 [Perplexity API Key](https://docs.perplexity.ai/)（可选）

### 30 秒体验

在 Claude Code 中输入：

```
/geo-optimizer 帮我生成一个 Organization Schema，品牌名叫"星辰科技"，做跨境电商AI选品的
```

或者分析一个网页：

```
/geo-content-optimizer https://your-website.com
```

---

## 功能详解

### Skill 1: geo-optimizer — 全流程 GEO 工具

通过 `/geo-optimizer` 触发，包含 5 大模块：

#### 模块 A：结构化数据生成

自动生成 7 类 JSON-LD Schema：

```
Organization    → 品牌实体："你是谁"
FAQPage         → FAQ 问答：43% AI 引用来源
TechArticle     → 文章结构化标记
Person          → 作者 E-E-A-T 可信度信号
@graph          → 作者+文章联合标记
Citation        → 权威来源引用标记
BreadcrumbList  → 导航层级结构
```

脚本用法：

```bash
# Organization Schema
python scripts/schema_generator.py --type organization \
  --name "品牌名" --description "描述" \
  --knows-about "领域1" "领域2" --offers "产品描述"

# FAQ Schema（从 JSON 文件读取）
python scripts/schema_generator.py --type faq --input faq_pairs.json

# 文章 Schema
python scripts/schema_generator.py --type article \
  --headline "标题" --author "作者" --date-published "2025-01-01"

# 输出带 <script> 标签的 HTML
python scripts/schema_generator.py --type organization \
  --name "品牌" --description "描述" --wrap
```

FAQ 输入文件格式：

```json
[
  {"question": "新手第一步应该做什么？", "answer": "具体答案，含数据..."},
  {"question": "A 和 B 有什么区别？", "answer": "具体答案，含案例..."}
]
```

#### 模块 B：内容 AI 可读性检测

```bash
python scripts/readability_checker.py --text "你的内容"
python scripts/readability_checker.py --file article.txt
python scripts/readability_checker.py --text "内容" --json
```

输出示例：

```
=== AI 可读性检查报告 ===
总段落数: 8
平均句长: 21字 [OK]
营销词命中: 无 OK
包含问句: [OK]
数据引用: 5个数字 [OK]
综合评分: 高 (6/7)
```

#### 模块 C：Pillar Page 集群规划

1 个核心主题 + 5-10 个子主题的内容架构，生成内部链接集群 HTML 和站点地图 JSON。

#### 模块 D：可见度测试与报告

支持双引擎：**Kimi**（默认，国内直连）和 **Perplexity**（海外）。

```bash
# 使用 Kimi 引擎（默认，国内直连）
python scripts/visibility_tester.py \
  --engine kimi \
  --brand "品牌名" \
  --keywords "关键词1" "关键词2" \
  --api-key "sk-xxxxx"

# 使用环境变量传 Key
export KIMI_API_KEY="sk-xxxxx"
python scripts/visibility_tester.py --brand "品牌名" --keywords "关键词"

# 使用 Perplexity 引擎
python scripts/visibility_tester.py \
  --engine perplexity \
  --brand "品牌名" \
  --keywords "关键词1" "关键词2" \
  --api-key "pplx-xxxxx"

# 自定义查询模板
python scripts/visibility_tester.py \
  --brand "高砖积木" \
  --keywords "积木品牌" "国产积木" \
  --query "{keyword}有哪些值得推荐的品牌？"

# 季度趋势报告
python scripts/geo_report_generator.py \
  --history visibility_history.json \
  --output report.md
```

**引擎对比：**

| 维度 | Kimi (默认) | Perplexity |
|------|-------------|------------|
| 国内可用性 | 直连，无需翻墙 | 需翻墙 |
| API 获取 | platform.moonshot.cn | perplexity.ai |
| SDK 依赖 | `openai` (`pip install openai`) | `requests` (`pip install requests`) |
| 搜索方式 | 内置 `$web_search` 联网搜索 | sonar-pro 模型 |
| 环境变量 | `KIMI_API_KEY` | `PERPLEXITY_API_KEY` |

#### 模块 E：内容差距分析

自动调用 `/geo-content-optimizer` 对比 Google AI Overview，找出内容缺口。

---

### Skill 2: geo-content-optimizer — 内容差距分析

通过 `/geo-content-optimizer <url>` 触发，零依赖，纯用 Claude 内置工具完成。

**工作流**：

```
抓取页面标题
  → Google 查询扩展（多角度搜索）
    → 提取核心搜索词
      → 获取 Google AI Overview
        → 搜索结果结构化摘要
          → 对比分析，生成优化建议报告
```

**输出**：

```
output/
  your-website-com/
    report.md                  ← 最终优化报告（对比表格 + 行动建议）
    ai_overview.md             ← Google AI Overview 内容
    query_fanout.md            ← 原始搜索扩展结果
    query_fanout_summary.md    ← 搜索结果摘要
```

---

## 项目结构

```
geo-start/
├── README.md                              ← 你正在看的文件
├── geo-optimizer.skill                    ← 可分发的 Skill 包
│
├── .claude/skills/
│   ├── geo-optimizer/                     ← GEO 全流程工具
│   │   ├── SKILL.md                       # 主技能文件（触发条件 + 工作流）
│   │   ├── scripts/
│   │   │   ├── schema_generator.py        # JSON-LD Schema 生成（7 种类型）
│   │   │   ├── readability_checker.py     # AI 可读性检测
│   │   │   ├── visibility_tester.py       # AI 可见度测试（Kimi / Perplexity 双引擎）
│   │   │   └── geo_report_generator.py    # 季度 GEO 报告
│   │   ├── references/
│   │   │   ├── geo-framework.md           # 10 步 GEO 框架完整参考
│   │   │   ├── schema-templates.md        # 9 类 Schema 模板
│   │   │   └── best-practices.md          # 最佳实践与部署清单
│   │   └── assets/
│   │       └── pillar-template.html       # Pillar Page 集群 HTML 模板
│   │
│   └── geo-content-optimizer/             ← 内容差距分析工具
│       ├── SKILL.md                       # 6 阶段分析工作流
│       └── README.md                      # 使用说明
```

---

## 使用场景

### 场景 1：首次 GEO 设置（全新品牌）

```
你：我有一个跨境电商的品牌叫"灵慧光智"，做 AI 选品工具的，怎么让 AI 搜索引擎引用我？

Claude：
  1. 收集品牌信息
  2. → 生成 Organization Schema
  3. → 引导创建 10 个 FAQ
  4. → 生成 FAQ Schema
  5. → 检测内容可读性
  6. → 规划内容集群
  7. → 首次可见度基线测试
  8. → 输出完整部署清单
```

### 场景 2：优化已有网页

```
你：/geo-content-optimizer https://my-site.com/article

Claude：自动完成 6 阶段分析，输出优化报告到 output/my-site-com/report.md
```

### 场景 3：月度监控

```
你：测试一下"灵慧光智"在 AI 搜索里的可见度

Claude：调用 Kimi 联网搜索，检测多个关键词，结果自动存入历史记录
```

### 场景 4：季度复盘

```
你：生成一份 GEO 季度报告

Claude：对比历史数据，输出引用率趋势 + 行动建议
```

---

## GEO 10 步框架速查

| 步骤 | 操作 | 对应工具 |
|------|------|---------|
| 1. 实体转型 | Organization Schema | `schema_generator.py` |
| 2. FAQ 生态 | ≥10 个 FAQ + Schema | `schema_generator.py` |
| 3. 口语化写作 | 去营销腔、加数据 | `readability_checker.py` |
| 4. 引用权威 | Citation Schema | `schema_generator.py` |
| 5. Schema 全部署 | Article/Breadcrumb 等 | `schema_generator.py` |
| 6. 内容集群 | Pillar Page 规划 | `pillar-template.html` |
| 7. 多格式嵌入 | 图片 alt + 视频字幕 | 参考 `best-practices.md` |
| 8. 可见度测试 | Kimi / Perplexity 双引擎 | `visibility_tester.py` |
| 9. E-E-A-T | 作者 Schema | `schema_generator.py` |
| 10. 季度迭代 | 趋势报告 | `geo_report_generator.py` |

---

## 常见问题

**Q：没有 API Key 能用吗？**

A：只有可见度测试（模块 D）需要 API Key，其余所有功能零依赖。没有 Key 时 Claude 会提供手动测试指引。

**Q：脚本需要安装第三方库吗？**

A：`visibility_tester.py` 使用 Kimi 引擎需要 `openai`（`pip install openai`），使用 Perplexity 需要 `requests`（`pip install requests`）。其他三个脚本纯标准库。

**Q：必须两个 Skill 都安装吗？**

A：不必须。`geo-optimizer` 可独立使用。安装 `geo-content-optimizer` 后获得模块 E（URL 内容差距分析）的能力。

**Q：支持哪些 AI 搜索引擎？**

A：可见度测试支持 Kimi（国内直连）和 Perplexity（海外）双引擎。GEO 框架设计覆盖 ChatGPT、Perplexity、Gemini、Google AI Overview。

**Q：Kimi 和 Perplexity 怎么选？**

A：国内用户首选 Kimi，直连无需翻墙，注册即用。海外用户或有 Perplexity 账号的可直接用 Perplexity。

---

## 贡献

欢迎提交 Issue 和 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add your feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 发起 Pull Request

### 特别感谢：

https://linux.do  佬友支持，

https://liang.348349.xyz/  更多agent项目

《Reddit GEO怎么做？10步AI搜索优化框架实战版》 https://mp.weixin.qq.com/s/q3oVi5BK6dl-7NYwkO97ug

## License

MIT License — 自由使用、修改和分发。
