from __future__ import annotations

import json
import time
from typing import Any, Dict

from fastapi.responses import StreamingResponse
from starlette.requests import Request
from starlette.responses import Content

from ..core import body_from_content_type, ensure_bytes, normalize_headers
from ..main import Monitor


async def _capture_response_bytes(response: StreamingResponse) -> bytes:
    chunks: list[Content] = [chunk async for chunk in response.body_iterator]
    body = ensure_bytes(chunks)

    async def _replay():
        for chunk in chunks:
            yield chunk

    response.body_iterator = _replay()
    return body


def instrument(monitor: Monitor, app, _AIKO_PKG_VERSION: str) -> None:
    @app.middleware("http")
    async def _aiko_mw(request: Request, call_next):
        start_ms = int(time.time() * 1000)

        req_headers = normalize_headers(dict(request.headers))
        try:
            req_body_raw = await request.body()
            req_body = json.loads(req_body_raw.decode("utf-8")) if req_body_raw else {}
        except Exception:
            req_body = {}

        try:
            response: StreamingResponse = await call_next(request)
            try:
                raw_res = await _capture_response_bytes(response)
            except Exception:
                raw_res = b""

            res_headers = normalize_headers(dict(response.headers))
            ctype = res_headers.get("content-type", "")
            try:
                res_body = body_from_content_type(ctype, raw_res)
            except Exception:
                res_body = None

            end_ms = int(time.time() * 1000)
            latency = max(0, end_ms - start_ms)
            full_url = str(request.url)
            endpoint = request.url.path
            if request.url.query:
                endpoint = f"{endpoint}?{request.url.query}"

            evt: Dict[str, Any] = {
                "url": full_url,
                "endpoint": endpoint,
                "method": request.method,
                "status_code": response.status_code,
                "request_headers": {**req_headers, "X-Aiko-Version": f"python:{_AIKO_PKG_VERSION}"},
                "request_body": req_body if req_body is not None else {},
                "response_headers": res_headers,
                "response_body": res_body,
                "duration_ms": latency,
            }

            monitor.add_event(evt)
            return response

        except Exception as exc:
            end_ms = int(time.time() * 1000)
            latency = max(0, end_ms - start_ms)
            full_url = str(request.url)
            endpoint = request.url.path
            if request.url.query:
                endpoint = f"{endpoint}?{request.url.query}"
            status_code = getattr(exc, "status_code", 500)

            evt: Dict[str, Any] = {
                "url": full_url,
                "endpoint": endpoint,
                "method": request.method,
                "status_code": status_code,
                "request_headers": {**req_headers, "X-Aiko-Version": f"python:{_AIKO_PKG_VERSION}"},
                "request_body": req_body if req_body is not None else {},
                "response_headers": {},
                "response_body": {"error": str(exc)},
                "duration_ms": latency,
            }

            monitor.add_event(evt)
            raise
