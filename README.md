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

## Roadmap
| version | milestone |
|---------|-----------|
| v0.1 | Single site crawler with CSV and Postgres sinks. |
| v0.2 | Multi-site scheduling and incremental crawl. |
| v0.3 | ES/Kafka sinks and optional web control plane. |
| v0.4 | Captcha solving hooks and fingerprint strategies. |
| v1.0 | Stable API and full documentation. |
