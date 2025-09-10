import random


def random_ua(pool: list[str] | None = None) -> str:
    pool = pool or [
        "Mozilla/5.0 (compatible; ConfCrawler/0.1)",
    ]
    return random.choice(pool)

