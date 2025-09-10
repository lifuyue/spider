# Agents 使用说明（Conf-Driven Crawler）

本仓库实现了一个配置驱动的爬虫引擎（Python 3.11+）。本文档聚焦“如何快速运行、调试与扩展”，并给出关键入口与常见问题说明。

## 快速开始
- 前置要求：
  - Python >= 3.11
  - 可选：`pytest` 用于运行测试（开发推荐）
- 安装依赖：
  - 项目当前无强制第三方依赖：`pip install -r requirements.txt`
- 试跑（不落盘）：
  - `python runners/run_site.py --config configs/site_demo.yml --dry-run`
- 正式运行（写入 CSV 与 SQLite）：
  - `python runners/run_site.py --config configs/site_demo.yml`
- 批量运行多站点：
  - `python runners/schedule.py --glob 'configs/*.yml'`

提示：默认示例配置将写入 `out/articles.csv` 与 `crawler.db`（SQLite）。

## 目录结构与入口
- 单站点入口：`runners/run_site.py`（解析参数并调用引擎）
- 调度入口：`runners/schedule.py`（按通配符批量执行配置）
- 引擎编排：`crawler_core/engine.py`（加载配置 → 调度 → 抓取 → 解析 → 归一化 → 去重 → 下游落盘）
- 配置校验（基础字段）：`crawler_core/config.py`
- 抓取器：`crawler_core/fetcher.py`（基于 `urllib` 的简单实现）
- 解析器：`crawler_core/extractor.py`（极简 CSS/正则候选）
- 归一化：`crawler_core/normalizer.py`（trim/lower/时间与时区/简单 HTML 清洗等）
- 去重：`crawler_core/dedupe.py`（内存集合）
- 管道（落盘）：
  - CSV：`crawler_core/pipelines/csv_sink.py`
  - DB（简化的 PG，测试用 SQLite 实现）：`crawler_core/pipelines/pg_sink.py`
- 配置示例与 Schema：
  - 示例：`configs/site_demo.yml`（注意：内容为 JSON 格式）
  - Schema：`configs/schema.json`（更完整字段定义，部分为预留能力）

## 运行方式
- 单站点：
  - `python runners/run_site.py --config <你的配置路径> [--dry-run]`
- 批量按通配：
  - `python runners/schedule.py --glob 'configs/*.yml'`
- 测试（开发态推荐）：
  - 安装：`pip install -U pytest`
  - 运行：`pytest -q`

## 配置要点（示例）
示例见 `configs/site_demo.yml`，尽管扩展名为 `.yml`，内容实际为 JSON：
- 基础字段：`name`、`base_url`、`entrypoints`、`items`、`pipelines` 必填（最低校验）。
- 入口 `entrypoints`：
  - 固定 URL：`{"url": "https://..."}`
  - 模板+范围：`{"url_template": "...{{page}}...", "range": {"start": 1, "stop": 5}}`
- 条目定义 `items`：
  - `match_url` 用于限定哪些页面解析该条目。
  - `fields` 字段支持多候选提取（`candidates`），示例：
    - CSS 取文本：`{"css": "h1.title::text"}`
    - CSS 取属性：`{"css": "time::attr(datetime)"}`
    - 正则：`{"regex": "..."}`
    - 固定来源：`{"from": "meta.url"}`
  - `normalize` 可指定一组归一化操作，如 `trim`、`lower`、`to_datetime:%Y-%m-%d %H:%M`、`to_tz:Asia/Shanghai`、`sanitize_html` 等。
  - `dedupe_keys` 指定去重键。
- 管道 `pipelines`：
  - CSV：`{"type": "csv", "path": "out/articles.csv"}`
  - DB（测试用 SQLite 文件）：`{"type": "db", "dsn": "sqlite:///crawler.db", "table": "articles", "upsert_keys": ["url"]}`

## 数据输出
- CSV：首行写表头，后续为追加写入，路径由配置 `path` 决定。
- DB（SQLite）
  - 初次写入自动建表；`upsert_keys` 用于唯一约束与 UPSERT 行为。
  - 检查数据示例：
    - `sqlite3 crawler.db "select count(*) from articles;"`

## 常见问题与限制
- 配置文件格式：当前实现使用 `json.loads` 读取配置，因此内容必须是 JSON 语法；示例虽然是 `.yml` 后缀，但请保持 JSON 格式。
- 渲染：`render.engine = playwright` 为预留能力，`crawler_core/renderers/playwright_runner.py` 仍为占位，未实现真实渲染。
- 反爬/限速/重试：`crawler_core/anti/*` 多为占位或简化实现，生产使用需补全。
- 抓取实现：基于 `urllib`，未内置代理池/UA 池动态切换等高级能力（有占位 API）。
- 解析器能力有限：仅覆盖了极简 CSS/正则示例，复杂站点需扩展。
- “PostgreSQL” 管道：当前以 SQLite 模拟，实际接入 PG 时需替换实现。

## 扩展点
- 自定义 Sink：在 `crawler_core/pipelines` 新增文件并在 `build_sinks` 中注册。
- 扩展解析：在 `Extractor._apply_candidate` 中新增候选类型（如 XPath/JsonPath/JMESPath）。
- 加强校验：在 `crawler_core/config.py` 中接入 JSON Schema/Pydantic 做完整校验（`configs/schema.json` 可复用）。
- 反爬与渲染：完善 `anti/*` 与 `renderers/*` 以支持真实限速/重试/代理与无头浏览器渲染。

## 合规与注意
- 尊重目标站点条款与 `robots.txt`；避免抓取敏感、受保护信息。
- 控制抓取频率与并发，减少对目标站点影响。

## 参考入口（便于查阅源码）
- 引擎编排：`crawler_core/engine.py:13`
- 单站点运行：`runners/run_site.py:6`
- 批量调度运行：`runners/schedule.py:7`
- 配置读取（JSON）：`crawler_core/config.py:17`
- 示例配置（JSON 内容）：`configs/site_demo.yml:1`

---
如需我继续：
- 生成你自己的站点配置模板
- 扩展解析/管道能力
- 接入真实 Playwright/代理/限速
请告诉我具体需求与目标站点示例。

