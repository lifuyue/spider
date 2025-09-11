import ssl
import time
import socket
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

# 全局硬超时，避免urllib在某些平台卡死
socket.setdefaulttimeout(20)

@dataclass
class FetchRequest:
    url: str
    headers: Optional[Dict[str, str]] = None
    method: str = "GET"
    data: Optional[bytes] = None

class Fetcher:
    def __init__(self, cfg: Any, timeout_s: int = 15):
        self.cfg = cfg
        self.timeout_s = timeout_s or 15
        self.default_headers = {
            "User-Agent": "confdriven-crawler/0.1 (+https://example.local)",
            "Accept": "*/*",
        }

    def _build_request(self, req: FetchRequest) -> urllib.request.Request:
        headers = dict(self.default_headers)
        if req.headers:
            headers.update(req.headers)
        r = urllib.request.Request(req.url, data=req.data, method=req.method)
        for k, v in headers.items():
            r.add_header(k, v)
        return r

    def get(self, req: Union[FetchRequest, Dict[str, Any], str]):
        if isinstance(req, dict):
            req = FetchRequest(url=req.get("url"), headers=req.get("headers"))
        elif isinstance(req, str):
            req = FetchRequest(url=req)
        elif isinstance(req, FetchRequest):
            pass
        elif hasattr(req, "url"):
            req = FetchRequest(url=getattr(req, "url"))
        else:
            req = FetchRequest(url=str(req))

        request = self._build_request(req)
        ctx = ssl.create_default_context()
        start = time.time()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s, context=ctx) as resp:  # pragma: no cover - network
                body = resp.read()
                return {
                    "url": req.url,
                    "status": getattr(resp, "status", 200),
                    "headers": dict(resp.headers.items()),
                    "content": body,
                    "text": body.decode(resp.headers.get_content_charset() or "utf-8", errors="replace"),
                    "elapsed": time.time() - start,
                }
        except KeyboardInterrupt:
            raise
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as e:
            return {
                "url": req.url,
                "error": str(e),
                "status": getattr(e, "code", None),
                "headers": {},
                "content": b"",
                "text": "",
                "elapsed": time.time() - start,
            }
