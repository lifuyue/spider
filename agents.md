# Agents 使用说明（Conf-Driven Crawler）

本节顶部新增：Scrapy + Playwright 架构升级计划（供 OpenAI Codex 执行）。原有配置驱动引擎说明仍保留于文档下半部分，方便参考与过渡。

---

## Scrapy + Playwright 架构升级（给 Codex）

目标：将当前仓库从“配置驱动引擎”迁移为 Scrapy + scrapy-playwright 的可运行项目，并新增 12306 余票查询 Spider。严格遵循“合规与边界”。本节提供依赖、骨架、示例代码片段、运行与自检清单，便于 Codex 一次性落盘改造。

### 0) 合规与边界（务必写入 README）
- 仅用于学习与自测，不得绕过验证码/登录/加密等访问控制，不得用于批量化影响对方服务。
- 真实环境查询需由用户在本地提供合法 Cookie/Headers，抓取频率极低（示例配置已限速）。
- 提供 MOCK_MODE（默认开启）使用本地/静态样本，CI/云端仅跑 Mock。

### 1) 依赖与项目骨架
1) 在 `requirements.txt`（或 `pyproject.toml`）加入/确认存在：
   - scrapy
   - scrapy-playwright
   - lxml
   - orjson（可选）
   - psycopg[binary]（或 psycopg2-binary，PG 可选）
   - pydantic（v1 或 v2，与项目一致）
   - python-dotenv（读取 .env）
   - pytest（可选）

2) 在仓库根创建 Scrapy 工程（保留原代码）：
```bash
scrapy startproject spiderx .
```
目标结构（与现有代码共存，settings 模块为 `spiderx`）：
```
spiderx/
  scrapy.cfg
  spiderx/
  __init__.py
  items.py
  middlewares.py
  pipelines.py
  settings.py
  spiders/
    __init__.py
```

3) `spiderx/settings.py` 基础反爬与 Playwright：
```python
BOT_NAME = "spiderx"
SPIDER_MODULES = ["spiderx.spiders"]
NEWSPIDER_MODULE = "spiderx.spiders"

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 2

DEFAULT_REQUEST_HEADERS = {
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "zh-CN,zh;q=0.9",
  "User-Agent": (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
  ),
}

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [403, 418, 429, 500, 502, 503, 504]
HTTPERROR_ALLOWED_CODES = [400, 401, 403, 418, 429, 500, 502, 503, 504]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 8.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

DOWNLOAD_TIMEOUT = 20

# Playwright
DOWNLOADER_MIDDLEWARES = {
  "scrapy_playwright.middleware.ScrapyPlaywrightDownloaderMiddleware": 543,
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 15000

# Pipelines（CSV 默认；PG 可选）
ITEM_PIPELINES = {
  "spiderx.pipelines.CsvPipeline": 300,
  # "spiderx.pipelines.PostgresPipeline": 400,  # 若 .env 配置了 PG 再开启
}

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
```

4) 在根目录新增 `.env.example`（用户复制为 `.env`）：
```dotenv
MOCK_MODE=true
# 如果需要真实查询，把上面改为 false，并提供合法 Cookie（如需）
AUTH_COOKIE_12306=
PG_DSN=postgresql://user:pass@localhost:5432/spiderx
```

### 2) Pipelines：CSV 与可选 PG
在 `spiderx/pipelines.py`：
```python
import os, csv, psycopg
from datetime import datetime

class CsvPipeline:
  def open_spider(self, spider):
    os.makedirs("out", exist_ok=True)
    self.fp = open(
      f"out/{spider.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
      "w",
      newline="",
      encoding="utf-8-sig",
    )
    self.writer = None

  def process_item(self, item, spider):
    if self.writer is None:
      self.writer = csv.DictWriter(self.fp, fieldnames=list(item.keys()))
      self.writer.writeheader()
    self.writer.writerow(dict(item))
    return item

  def close_spider(self, spider):
    if getattr(self, "fp", None):
      self.fp.close()


class PostgresPipeline:
  def open_spider(self, spider):
    dsn = os.getenv("PG_DSN")
    if not dsn:
      raise RuntimeError("PG_DSN not set")
    self.conn = psycopg.connect(dsn)
    self.conn.execute(
      """
    CREATE TABLE IF NOT EXISTS ticket_left (
      dt date,
      from_station text,
      to_station text,
      train_no text,
      seat_type text,
      left_count int,
      raw jsonb
    );"""
    )
    self.conn.commit()

  def process_item(self, item, spider):
    with self.conn.cursor() as cur:
      cur.execute(
        """
      INSERT INTO ticket_left (dt, from_station, to_station, train_no, seat_type, left_count, raw)
      VALUES (%(date)s, %(from)s, %(to)s, %(train_no)s, %(seat_type)s, %(left_count)s, %(raw)s::jsonb)
      """,
        {
          "date": item.get("date"),
          "from": item.get("from_station"),
          "to": item.get("to_station"),
          "train_no": item.get("train_no"),
          "seat_type": item.get("seat_type"),
          "left_count": item.get("left_count"),
          "raw": item.get("raw_json"),
        },
      )
    self.conn.commit()
    return item

  def close_spider(self, spider):
    if getattr(self, "conn", None):
      self.conn.close()
```

### 3) Spider：12306 余票（支持 Mock/真实、参数化）
在 `spiderx/spiders/tickets_12306.py`：
```python
import os, json
import scrapy
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Tickets12306Spider(scrapy.Spider):
  name = "tickets_12306"

  def __init__(self, date=None, from_=None, to=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.query_date = date or datetime.now().strftime("%Y-%m-%d")
    self.from_code = (from_ or kwargs.get("from") or "BJP").upper()
    self.to_code = (to or "SHH").upper()
    self.mock = (os.getenv("MOCK_MODE", "true").lower() in ("1","true","yes"))
    self.auth_cookie = os.getenv("AUTH_COOKIE_12306") or ""

  def start_requests(self):
    if self.mock:
      p = os.path.join("tests", "fixtures", "12306_left_ticket.json")
      assert os.path.exists(p), f"missing fixture: {p}"
      yield scrapy.Request(
        url=f"file://{os.path.abspath(p)}",
        callback=self.parse_file,
        dont_filter=True,
      )
    else:
      base = os.getenv("TICKET_API_BASE", "https://kyfw.12306.cn/otn/leftTicket/query")
      params = {
        "leftTicketDTO.train_date": self.query_date,
        "leftTicketDTO.from_station": self.from_code,
        "leftTicketDTO.to_station": self.to_code,
        "purpose_codes": "ADULT",
      }
      url = f"{base}?{urlencode(params)}"
      headers = {}
      if self.auth_cookie:
        headers["Cookie"] = self.auth_cookie
      yield scrapy.Request(
        url=url,
        callback=self.parse_json,
        headers=headers,
        meta={"playwright": False},
      )

  def parse_file(self, response):
    data = json.loads(response.text)
    yield from self._yield_items(data)

  def parse_json(self, response):
    try:
      data = json.loads(response.text)
    except Exception as e:
      self.logger.warning("JSON decode failed: %s", e)
      return
    yield from self._yield_items(data)

  def _yield_items(self, data):
    # 经典结构：data.result 为“|”分隔长串，data.map 映射站码→站名
    result = (data.get("data") or {}).get("result") or []
    station_map = (data.get("data") or {}).get("map") or {}

    for row in result:
      parts = row.split("|")
      # 位序需与样本对齐：下面仅示意，按 fixture 调整
      train_no = parts[3]
      from_code = parts[6]
      to_code = parts[7]
      seats = {
        "YZ": parts[29],   # 硬座（示意）
        "YW": parts[28],   # 硬卧（示意）
        "ZE": parts[30],   # 二等座（示意）
        "ZY": parts[31],   # 一等座（示意）
        "SWZ": parts[32],  # 商务座（示意）
      }

      for seat_type, left_val in seats.items():
        yield {
          "date": self.query_date,
          "from_station": station_map.get(from_code, from_code),
          "to_station": station_map.get(to_code, to_code),
          "train_no": train_no,
          "seat_type": seat_type,
          "left_count": self._normalize_left(left_val),
          "raw_json": json.dumps(row, ensure_ascii=False),
        }

  @staticmethod
  def _normalize_left(v):
    v = (v or "").strip()
    if v.isdigit():
      return int(v)
    if v in ("有",):
      return 50
    if v in ("无", "--", "—", "–"):
      return 0
    return -1
```

在 `tests/fixtures/12306_left_ticket.json` 放置最小可解析样本（示例）：
```json
{
  "data": {
  "result": [
    "|预留|D1234|D1234|BJP|SHH|BJP|SHH|06:30|12:10|05:40|Y|Bvja5...|...|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|20|15|有|无|--|"
  ],
  "map": {"BJP": "北京", "SHH": "上海"}
  }
}
```

### 4) 可选：Playwright 用于“需要渲染的路由”
示例新建 `spiderx/spiders/station_codes_demo.py`，仅在 `-a demo=true` 时启用：
```python
import scrapy

class StationCodesDemo(scrapy.Spider):
  name = "station_codes_demo"

  def __init__(self, demo=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.demo = str(demo or "false").lower() in ("1","true","yes")

  def start_requests(self):
    if not self.demo:
      self.logger.info("demo flag not set; skipping")
      return
    yield scrapy.Request(
      url="https://kyfw.12306.cn/",
      meta={
        "playwright": True,
        "playwright_page_methods": [("wait_for_selector", "table")],
      },
      callback=self.parse_page,
    )

  def parse_page(self, response):
    # 示例：提取表格行
    for tr in response.css("table tr"):
      yield {
        "cols": tr.css("td::text").getall(),
      }
```

### 5) 命令与 README 更新（供用户运行）
在 README 中加入：
```bash
# 安装依赖
pip install -r requirements.txt

# 创建 .env（默认 MOCK_MODE=true）
cp .env.example .env

# 跑 Mock（不会访问真实 12306）
scrapy crawl tickets_12306 -a date=2025-10-01 -a from=BJP -a to=SHH

# 真实查询（需提供合法 Cookie，谨慎限速）
# 编辑 .env: MOCK_MODE=false, AUTH_COOKIE_12306=xxxxx
scrapy crawl tickets_12306 -a date=2025-10-01 -a from=BJP -a to=SHH

# 可选：演示 Playwright 页面渲染
scrapy crawl station_codes_demo -a demo=true
```
说明反爬策略：低并发、限速、重试、自动节流、稳定 UA（可扩展 UA 池）、可选代理（.env 增加 PROXY_URL 后在 settings 启用）。

### 6) 自检与回显（必须执行并粘贴输出）
1. 打印 Python 与 Scrapy 版本：
```bash
python -V && python -c "import scrapy; print(scrapy.__version__)"
```
2. 确认 spider 列表：
```bash
scrapy list  # 应包含 tickets_12306 与 station_codes_demo
```
3. 运行 Mock 模式并展示 CSV 前 5 行：
```bash
scrapy crawl tickets_12306 -a date=2025-10-01 -a from=BJP -a to=SHH
head -n 5 out/tickets_12306_*.csv
```
4. 打印关键日志（请求数、解析条数、重试次数）。
5. 若启用 PostgresPipeline：插入一次并打印表行数。

---

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

