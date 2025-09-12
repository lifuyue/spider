# AI Agent 工作准则与快捷清单（务必先读）

本节为面向 AI 编程助手的执行准则与快捷操作，目的是在当前仓库中“少动、准改、快验”。若与具体任务冲突，请优先澄清后再动手。

## Do / Don't（行为准则）
- Do: 聚焦最小可行改动，保持接口与风格一致；必要时补足文档。
- Do: 优先复用既有模块与约定（见“结构地图”）；新增文件放在正确目录。
- Do: 对改动点进行局部测试与静态检查（只跑受影响文件/用例）。
- Do: 覆盖关键边界与错误分支，添加最小必要单测或样例。
- Do: 变更前先搜索相近实现，遵循已有命名/日志/错误处理方式。
- Don't: 引入不必要的依赖或重构无关代码；避免大而散的提交。
- Don't: 硬编码易变/共享常量（颜色、主题 token、连接串等）。
- Don't: 在不确定需求或存在冲突时盲目实现——先询问或提交草案。

## Commands / 局部与快速命令（zsh）
- 安装依赖：
	```zsh
	pip install -r requirements.txt
	```
- 仅运行单测文件：
	```zsh
	pytest -q tests/test_extractor.py
	```
- 仅运行某个测试用例：
	```zsh
	pytest -q tests/test_extractor.py::test_css_text
	```
- 以关键字筛选测试：
	```zsh
	pytest -q -k extractor
	```
- 语法快速检查（无类型检查依赖时）：
	```zsh
	python -m compileall crawler_core/extractor.py
	```
- 可选：若已安装 black/ruff/mypy，仅对改动文件进行检查（示例）：
	```zsh
	# 可选安装
	pip install black ruff mypy
	# 定向检查
	ruff check crawler_core/extractor.py
	black --check crawler_core/extractor.py
	mypy crawler_core --strict --python-version 3.11
	```

## Project Structure 简述（结构地图）
- `configs/`: 站点配置与 Schema（注意示例虽为 `.yml`，内容是 JSON 语法）。
- `crawler_core/`: 配置驱动引擎核心：
	- `engine.py`: 编排入口；`scheduler.py`: 调度；`fetcher.py`: 抓取；`extractor.py`: 解析。
	- `normalizer.py`: 归一化；`dedupe.py`: 去重；`pipelines/`: CSV/DB 落盘。
	- `anti/`: 反爬占位（UA/限速/重试/代理）；`renderers/`: 渲染占位。
- `runners/`: 运行入口脚本（单站点/批量）。
- `offline/`: 本地样本/离线页面。
- `tests/`: 单元测试与夹具。
- 计划扩展（Scrapy 迁移）：`spiderx/`（见下文“Scrapy + Playwright 架构升级”）。

## Good / Bad Examples（简要）
- 好：在 `crawler_core/extractor.py` 新增解析分支，同时添加对应最小测试 `tests/test_extractor.py`，仅跑该文件验证。
- 坏：为了支持一个字段，重构 `engine.py` 大片逻辑并改动所有调用方。
- 好：新增管道时放在 `crawler_core/pipelines/`，并在现有构建函数注册；保持与 `csv_sink.py` 接口一致。
- 坏：临时把写文件逻辑塞进 `engine.py`，导致职责混乱。
- 好：新增配置字段先更新 `configs/schema.json` 并在 `config.py` 做校验；给出一个最小 `configs/*.yml` 示例。

## When Stuck / Clarify First（先澄清）
- 规格不清晰、存在冲突或多种实现路径时：先提出“最小草案”与影响面，等待确认。
- 需要新增依赖或大幅改动结构：先给出选型、兼容性与迁移步骤，再行动。
- 外部受限（登录/验证码/反爬）场景：遵循合规边界，默认使用 Mock/离线样本。

## Preferred Tools / Libraries（最少且优先复用）
- 依赖以 `requirements.txt` 为准：`pytest`、`lxml`、`httpx`、`pydantic`、`structlog` 等已存在即可复用。
- 日志：沿用 `crawler_core/logger.py` 的既有风格与字段。
- 测试：`pytest`；断言与夹具复用现有模式；优先文件级/用例级运行。
- 如需页面渲染或更复杂抓取：按本文后段“Scrapy + scrapy-playwright 迁移计划”执行；CI/云端仅跑 Mock。

## Minimal Tests Requirement（最小测试要求）
- 对“功能性改动”必须有最小单测覆盖：正常路径 + 至少一个错误/边界分支。
- 新增配置/字段：需校验更新与失败用例（无效输入/缺字段）。
- 新增解析/管道：提供一个离线/Mock 样本，保证可重复、可在本地快速跑通。
- 回归风险：若改动影响关键路径（抓取/解析/落盘），需在相关测试文件中补充断言。

## 提示/原则（执行时随手检查）
- 优先文件级检查（lint/type/test）而不是全项目运行，获得最快反馈。
- 避免硬编码那些常变/共享的东西（样式颜色/主题 token/连接串/路径）。
- 动手前先找可复用组件/实现，保持风格与命名一致。
- 输出代码前自检：是否覆盖边界/错误情况？是否引入无关改动？
- 任务粒度小、提交聚焦；大改分步提交，并在文档/PR 说明影响面与回滚策略。
- UI/样式相关任务需遵循既有设计/主题，不要随意引入新样式或组件。

# Agents 使用说明（Conf-Driven Crawler）
