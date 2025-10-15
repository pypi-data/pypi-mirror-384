from __future__ import annotations

import base64
import gzip
import hashlib
import hmac
import json
import re
from typing import Any, Dict, Mapping, Union

REDACTION_MASK = "[REDACTED]"
SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "cookie",
    "email",
    "phonenumber",
    "ssn",
    "creditcard",
    "set-cookie",
    "ip",
    "x-forwarded-for",
    "x-forwarded-ip",
    "x-real-ip",
    "cf-connecting-ip",
    "true-client-ip",
    "forwarded",
    "remote-addr",
    "client-ip",
}
PII_REGEXES = [
    re.compile(r"[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b", re.IGNORECASE),
]

Redactable = Union[
    str,
    int,
    float,
    bool,
    None,
    list["Redactable"],
    Mapping[str, "Redactable"],
]


def redact_any(x: Redactable) -> Redactable:
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
                out[k] = REDACTION_MASK
            else:
                out[k] = redact_any(v)
        return out
    if isinstance(x, list):
        return [redact_any(i) for i in x]
    if isinstance(x, str):
        s = x
        for rgx in PII_REGEXES:
            s = rgx.sub(REDACTION_MASK, s)
        return s
    return x


def redact_event(evt):
    return {
        "endpoint": evt["endpoint"],
        "method": evt["method"],
        "status_code": evt["status_code"],
        "request_headers": redact_any(normalize_headers(evt["request_headers"])),
        "request_body": redact_any(evt["request_body"]),
        "response_headers": redact_any(normalize_headers(evt["response_headers"])),
        "response_body": redact_any(evt["response_body"]),
        "duration_ms": evt["duration_ms"],
        "url": evt["url"],
    }


def try_json(buf: bytes | None):
    if not buf:
        return {}
    try:
        import json

        return json.loads(buf.decode("utf-8"))
    except Exception:
        return safe_text(buf)


def safe_text(buf: bytes):
    try:
        return buf.decode("utf-8")
    except Exception:
        return {"base64": buf.hex()}


def body_from_content_type(ct: str, raw: bytes):
    ct = (ct or "").lower()
    if "application/json" in ct:
        try:
            import json

            return json.loads(raw.decode("utf-8"))
        except Exception:
            return raw.decode("utf-8", errors="ignore")
    if ct.startswith("text/") or "html" in ct or "xml" in ct:
        return raw.decode("utf-8", errors="ignore")
    return {"base64": raw.hex()}


def normalize_headers(headers: Dict[str, Any] | None) -> Dict[str, str]:
    if not headers:
        return {}
    out: Dict[str, str] = {}
    for k, v in headers.items():
        if v is None:
            continue
        if isinstance(v, list):
            out[str(k).lower()] = ", ".join(str(x) for x in v)
        else:
            out[str(k).lower()] = str(v)
    return out


def sign(secret_bytes: bytes, data: bytes) -> str:
    return hmac.new(secret_bytes, data, hashlib.sha256).hexdigest()


# only for testing, just making sure sign is good
def verify(secret_bytes: bytes, data: bytes, hex_sig: str) -> bool:
    try:
        expected = hmac.new(secret_bytes, data, hashlib.sha256).digest()
        provided = bytes.fromhex(hex_sig)
        if len(provided) != len(expected):
            return False
        return hmac.compare_digest(expected, provided)
    except Exception:
        return False


def gzip_event(event: Dict[str, Any]) -> bytes:
    payload = json.dumps(event).encode("utf-8")
    return gzip.compress(payload)


def b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def ensure_bytes(parts: list[Any]) -> bytes:
    buf = bytearray()
    for p in parts:
        if isinstance(p, (bytes, bytearray)):
            buf += p
        else:
            buf += str(p).encode("utf-8", errors="replace")
    return bytes(buf)
