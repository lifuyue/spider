from __future__ import annotations

def _fmt(fields: dict[str, object]) -> str:
    return " ".join(f"{k}={v}" for k, v in fields.items())

def info(tag: str, **fields: object) -> None:
    print(f"[{tag}][ok] {_fmt(fields)}")

def warn(tag: str, **fields: object) -> None:
    print(f"[{tag}][warn] {_fmt(fields)}")

def error(tag: str, **fields: object) -> None:  # pragma: no cover - trivial
    print(f"[{tag}][err] {_fmt(fields)}")

__all__ = ["info", "warn", "error"]
