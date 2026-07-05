# CodeTruth — AI生成代码信任与验证平台

> 弥合AI代码生成与生产部署之间的关键信任鸿沟。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 什么是 CodeTruth？

**CodeTruth** 是首个专为弥合AI生成代码与生产部署之间信任鸿沟而设计的开源平台。随着AI编码工具以前所未有的速度输出代码，开发团队面临一个严峻的挑战：**如何信任不是自己写的代码？**

CodeTruth 提供了这个缺失的基础设施层——来源追踪、多维度信任评分、知识图谱分析、质量门控流水线和持久化记忆——使AI生成的代码变得可审计、可验证、可信任。

### 为什么需要 CodeTruth？

- **96%的开发者**不完全信任AI生成的代码
- **AI工具使代码产出增加55%**，但审核能力未能同步增长
- **Agent多步骤任务成功率**仅有77%
- **目前没有标准**用于追踪AI代码的来源和质量

CodeTruth 通过构建AI编码生态急需的**治理层**来解决这些问题。

## 核心功能

### 来源追踪引擎
追踪每一块AI生成代码的完整谱系——哪个模型、什么提示词、何时生成、在什么上下文中。永不错失"谁写了什么"的追踪链。

### 信任评分引擎
跨**6个维度**的多维度质量评估：质量、安全、可测试性、性能、文档、可维护性。为每个代码块获取客观的信任分数（0-100）。

### 代码知识图谱
基于AST的依赖关系映射，展示类、函数、导入和调用链。理解AI代码如何与现有代码库连接。

### 质量门控流水线
可配置的验证检查点，包含**10条内置规则**，覆盖安全、质量和架构。阻止不符合标准的部署。

### Token优化器
智能上下文压缩，**节省60-95%的Token**同时保留语义含义。大幅降低AI API成本。

### 记忆层
持久化上下文记忆，采用结构化记忆元组（谁/什么/何时/何地/为何）。AI工具跨会话记住你的代码库。

## 5W1H 架构

| 维度 | 描述 |
|-----------|-------------|
| **What（是什么）** | AI生成代码信任与验证平台 |
| **Why（为什么）** | 96%的开发者不信任AI代码；缺乏标准的治理机制 |
| **Who（谁用）** | 开发团队、工程经理、DevOps、安全团队 |
| **When（何时用）** | 集成到CI/CD流水线、pre-commit钩子和PR审核中 |
| **Where（在哪用）** | CLI、REST API、IDE插件、CI/CD集成 |
| **How（如何做）** | 来源追踪 + 信任评分 + 知识图谱 + 质量门控 |

## 快速开始

### 安装

```bash
pip install codetruth
```

### CLI使用

```bash
# 分析文件的信任评分
codetruth analyze src/main.py

# 扫描整个目录
codetruth scan ./src

# 优化Token以供AI使用
codetruth optimize src/main.py --strategy moderate

# 生成综合报告
codetruth report

# 启动API服务器
codetruth serve
```

### Python API

```python
from codetruth.engine.scoring import TrustScoringEngine
from codetruth.engine.optimizer import TokenOptimizer

# 分析代码信任度
engine = TrustScoringEngine()
score = engine.assess("func1", "calculate_sum", "function", code, "python")
print(f"信任分数: {score.overall_score}/100")

# 为AI优化
optimizer = TokenOptimizer()
result = optimizer.auto_optimize(large_code)
print(f"节省 {result.tokens_saved} tokens ({result.compression_ratio:.0%})")
```

### REST API

```bash
# 启动服务
codetruth serve

# 分析代码
curl -X POST http://localhost:8742/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): return \"world\"", "language": "python"}'

# API文档: http://localhost:8742/docs
```

## 项目结构

```
github_big_proj17/
├── codetruth/              # 主包
│   ├── config/             # 配置管理
│   ├── engine/             # 核心引擎
│   │   ├── provenance/     # 代码来源追踪
│   │   ├── graph/          # 知识图谱
│   │   ├── scoring/        # 信任评分
│   │   └── optimizer/      # Token压缩
│   ├── memory/             # 持久化记忆层
│   ├── gates/              # 质量门控流水线
│   ├── cli/                # 命令行界面
│   ├── api/                # FastAPI REST API
│   └── web/                # Web仪表盘
├── tests/                  # 测试套件
├── frontend/               # Web仪表盘 (React)
├── docs/                   # 文档
├── skills/                 # 内置技能
├── examples/               # 使用示例
└── pyproject.toml          # 项目配置
```

## 灵感来源

CodeTruth 汲取了多个开创性开源项目的设计精华：

- **Hermes Agent** (179K stars): 具有持久化记忆的Agent架构
- **CodeGraph** (21K stars): 基于AST的依赖分析，减少57%的Token使用
- **SuperMemory** (25K stars): 结构化记忆元组模型
- **Headroom** (10K stars): 节省60-95% Token的上下文压缩
- **PR-Agent**: 自动化代码审核和质量门控
- **ECC** (205K stars): 多层AI编程平台架构

## 路线图

- [x] 核心引擎（来源追踪、评分、图谱、优化器）
- [x] 质量门控流水线
- [x] REST API 和 CLI
- [x] Web仪表盘
- [ ] IDE插件（VS Code、JetBrains）
- [ ] GitHub/GitLab CI/CD集成
- [ ] 基于向量的语义搜索
- [ ] 多语言支持（JS/TS、Java、Rust、Go）
- [ ] 团队风险仪表盘
- [ ] 区块链锚定的来源追踪（不可篡改的审计链）
- [ ] LLM作为裁判的自动代码审核

## 技术栈

- **后端**: Python 3.10+, FastAPI, Pydantic
- **数据库**: SQLite（默认）, LanceDB（向量）, PostgreSQL（生产环境）
- **前端**: React, Tailwind CSS
- **CLI**: Click, Rich
- **测试**: pytest, coverage
- **代码质量**: Black, Ruff, mypy

## 参与贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎所有形式的贡献——代码、文档、问题和想法！

```bash
git clone https://github.com/lanekingkong/codetruth.git
cd codetruth
pip install -e ".[dev]"
pre-commit install
pytest
```

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

<p align="center">
  <b>CodeTruth</b> — 让AI生成的代码可审计、可验证、可信任。
</p>