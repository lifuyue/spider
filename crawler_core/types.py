from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Request:
    url: str
    method: str = "GET"
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    url: str
    status: int
    text: str

