# Conf-Driven Crawler

A configuration-driven, extensible web crawling engine for Python 3.11+.

## Features
- Configuration driven via YAML/JSON.
- Optional Playwright rendering.
- Extraction DSL with CSS/XPath/Regex/JsonPath/JMESPath.
- Normalization pipeline.
- Deduplication and incremental crawling.
- Pluggable sinks (CSV, PostgreSQL).
- Config validation with JSON Schema and Pydantic.
- Basic telemetry counters.
- CLI runners for single site and scheduler.

## Quick Start
```bash
pip install -r requirements.txt
python runners/run_site.py --config configs/site_demo.yml --dry-run
```

## Security & Compliance
- Respect target site terms and `robots.txt`.
- Do not crawl protected or private data.
- Use responsibly and evaluate legal compliance before production use.

## Douban Top 250
- For learning only; respect Douban site terms and robots.
- Keep crawl frequency low (config limits QPS) to minimize impact.
- Do not redistribute or commercialize scraped data.

### 运行说明
```bash
# 干跑：仅解析不落盘
DRY_RUN=true python runners/douban_top250.py

# 或使用通用入口
python runners/run_site.py --config configs/douban_top250.yml --dry-run

# 实际运行将写入 out/douban_top250.csv
python runners/douban_top250.py
```

配置中已将 `request.rate_limit.domain_qps` 设为 `0.5`、`concurrency` 设为 `2`，请勿提升速率；输出目录 `out/` 已在 `.gitignore` 中忽略。

## Roadmap
| version | milestone |
|---------|-----------|
| v0.1 | Single site crawler with CSV and Postgres sinks. |
| v0.2 | Multi-site scheduling and incremental crawl. |
| v0.3 | ES/Kafka sinks and optional web control plane. |
| v0.4 | Captcha solving hooks and fingerprint strategies. |
| v1.0 | Stable API and full documentation. |
