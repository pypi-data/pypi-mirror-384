import base64
import gzip
import json
from typing import Any, cast

import pytest

from src.aiko_monitor.core import (
    b64url_decode,
    body_from_content_type,
    ensure_bytes,
    gzip_event,
    normalize_headers,
    redact_any,
    redact_event,
    safe_text,
    sign,
    try_json,
    verify,
)


def test_normalize_headers():
    headers = {"Content-Type": "application/json", "X-Test": ["a", "b"], "Noney": None}
    result = normalize_headers(headers)
    assert result["content-type"] == "application/json"
    assert result["x-test"] == "a, b"
    assert "Noney".lower() not in result


def test_normalize_headers_edge_cases():
    headers = {123: "value", "": "empty_key", "valid": ""}
    result = normalize_headers(headers)
    assert result["123"] == "value"
    assert result[""] == "empty_key"
    assert result["valid"] == ""


def test_ensure_bytes_with_mixed_types():
    parts = [b"abc", "def", 123]
    result = ensure_bytes(parts)
    assert isinstance(result, bytes)
    assert b"abc" in result and b"def" in result and b"123" in result


def test_b64url_decode():
    data = b"hello world"
    encoded = base64.urlsafe_b64encode(data).decode().rstrip("=")
    decoded = b64url_decode(encoded)
    assert decoded == data


@pytest.mark.parametrize(
    "pk,sk_b64url,data,expected_hex",
    [
        (
            "pk_bcbWWw2TDrUEpDVfuygbtg",
            "djlXfG5bui6WOxCegNYl3C45d03r8z8gj3Tj3q9JCWA",
            "hello",
            "961de8beee5e76cda1b594f78477dd108e67eb3b90690839b1bcc65eae6d678a",
        ),
        (
            "pk_U4717xM6ZZJE4NQEqCy6iA",
            "HtvkaOMkRUTRsOXUngykx44gV71YCApJWvIhJRM6nWc",
            "hello",
            "9a1cf5e2c1481be12eb333f3072951532732a9c6c4deeedf07ec762cf3816d17",
        ),
    ],
)
def test_verify_against_known_vectors(pk, sk_b64url, data, expected_hex):
    secret = b64url_decode(sk_b64url)
    msg = data.encode()
    actual = sign(secret, msg)
    assert actual == expected_hex
    assert verify(secret, msg, actual) is True
    assert verify(secret, msg, expected_hex) is True


def test_verify_rejects_wrong_secret_and_bad_hex():
    secret_ok = b"abc"
    secret_bad = b"abcd"
    data = b"payload"
    good_sig = sign(secret_ok, data)
    assert verify(secret_ok, data, good_sig) is True
    assert verify(secret_bad, data, good_sig) is False
    assert verify(secret_ok, data, "zz-not-hex-zz") is False
    assert verify(secret_ok, data, good_sig[:-2]) is False


def test_body_from_content_type_json_and_text():
    raw_json = b'{"x": 1}'
    out_json = body_from_content_type("application/json", raw_json)
    assert out_json == {"x": 1}

    raw_text = b"<html></html>"
    out_text = body_from_content_type("text/html", raw_text)
    assert "<html>" in out_text

    raw_bin = b"\x00\x01\x02"
    out_bin = body_from_content_type("application/octet-stream", raw_bin)
    assert out_bin == {"base64": raw_bin.hex()}


def test_body_from_content_type_invalid_utf8():
    invalid_utf8 = b"\x80\x81\x82\x83"
    result = body_from_content_type("text/plain", invalid_utf8)
    assert isinstance(result, str)

    result_json = body_from_content_type("application/json", invalid_utf8)
    assert isinstance(result_json, str)


def test_body_from_content_type_empty():
    assert body_from_content_type("application/json", b"") == ""
    assert body_from_content_type("text/html", b"") == ""
    assert body_from_content_type("application/octet-stream", b"") == {"base64": ""}


def test_try_json_and_safe_text():
    assert try_json(b'{"a":2}') == {"a": 2}
    assert try_json(b"not-json") == "not-json"
    assert try_json(None) == {}


def test_safe_text_directly():
    assert safe_text(b"hello") == "hello"
    assert safe_text(b"\xff\xfe") == {"base64": "fffe"}


def test_redact_any_case_insensitive_keys():
    data = {"PASSWORD": "secret1", "Api_Key": "key123", "Authorization": "Bearer xyz"}
    red = cast(dict[str, Any], redact_any(data))
    assert red["PASSWORD"] == "[REDACTED]"
    assert red["Api_Key"] == "[REDACTED]"
    assert red["Authorization"] == "[REDACTED]"


def test_redact_any_multiple_pii_in_string():
    data = {"message": "Contact john@example.com or ping 203.0.113.1 for info"}
    red = cast(dict[str, Any], redact_any(data))
    assert red["message"].count("[REDACTED]") == 2


def test_redact_event_deeply_nested():
    evt = {
        "endpoint": "/foo",
        "method": "POST",
        "status_code": 201,
        "request_headers": {
            "Authorization": "Bearer abc",
            "X-Forwarded-For": "203.0.113.1",
        },
        "request_body": {
            "ssn": "123-45-6789",
            "profile": {
                "email": "user@example.com",
                "contacts": [
                    {"phoneNumber": "+1 (415) 555-9999"},
                    {"note": "call +1-555-000-1111 or email boss@example.org"},
                ],
            },
        },
        "response_headers": {
            "Set-Cookie": "id=1",
        },
        "response_body": {
            "user": {
                "credentials": {"token": "abcd1234"},
                "emails": ["a@b.com", "c@d.org"],
                "info": "ipv6=2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            },
        },
        "duration_ms": 42,
        "url": "http://x/y?z=1",
    }

    red = cast(dict[str, Any], redact_event(evt))

    assert red["request_headers"]["authorization"] == "[REDACTED]"
    assert red["request_headers"]["x-forwarded-for"] == "[REDACTED]"
    assert red["request_body"]["ssn"] == "[REDACTED]"
    assert red["response_headers"]["set-cookie"] == "[REDACTED]"
    assert red["response_body"]["user"]["credentials"]["token"] == "[REDACTED]"
    assert red["request_body"]["profile"]["email"] == "[REDACTED]"
    assert "[REDACTED]" in red["request_body"]["profile"]["contacts"][1]["note"]
    assert all(e == "[REDACTED]" for e in red["response_body"]["user"]["emails"])
    assert red["response_body"]["user"]["info"] == "ipv6=[REDACTED]"


def test_gzip_event():
    event = {"a": 1, "b": "c"}
    blob = gzip_event(event)
    decoded = json.loads(gzip.decompress(blob).decode("utf-8"))
    assert decoded == event
