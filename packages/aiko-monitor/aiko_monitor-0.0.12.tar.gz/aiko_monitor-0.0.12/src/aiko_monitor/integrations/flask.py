from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, g, request

from ..core import body_from_content_type, normalize_headers, try_json
from ..main import Monitor


def instrument(monitor: Monitor, app: Flask, _AIKO_PKG_VERSION: str) -> None:
    @app.before_request
    def _aiko_before():
        g._aiko_start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        try:
            request.get_data(cache=True, as_text=False)
        except Exception:
            pass

    @app.after_request
    def _aiko_after(response):
        try:
            start_ms = getattr(g, "_aiko_start_ms", int(datetime.now(timezone.utc).timestamp() * 1000))
            end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            latency = max(0, end_ms - start_ms)

            req_headers = normalize_headers(dict(request.headers))
            res_headers = normalize_headers(dict(response.headers))

            try:
                raw_body = request.get_data(cache=True)
                req_body = try_json(raw_body)
            except Exception:
                req_body = {}

            try:
                raw_res = response.get_data(as_text=False)
                res_body = body_from_content_type(res_headers.get("content-type", ""), raw_res)
            except Exception:
                res_body = None

            endpoint = request.full_path
            if endpoint.endswith("?"):
                endpoint = endpoint[:-1]

            evt = {
                "url": request.url,
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
        except Exception:
            pass
        return response
