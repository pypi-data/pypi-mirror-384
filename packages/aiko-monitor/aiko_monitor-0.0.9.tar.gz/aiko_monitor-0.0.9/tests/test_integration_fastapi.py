import asyncio

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.testclient import TestClient

from src.aiko_monitor.main import Monitor
from tests.mock_server import MockMonitorServer, wait_for


@pytest.fixture
def fastapi_fixture():
    secret = "aNlvpEIXkeEubNgikWXyGnh8LyXa72yZhR9lEmzgHCM"
    project_key = "pk_92Yb_kCIwRhy06UF-FQShg"

    mock_server = MockMonitorServer(port=0, secret=secret, project_key=project_key)
    mock_server.start_sync()

    app = FastAPI()

    monitor = Monitor(
        app,
        project_key=project_key,
        secret_key=secret,
        endpoint=f"http://localhost:{mock_server.port}/api/monitor/ingest",
        enabled=True,
    )

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return "<html><body><h1>hello</h1></body></html>"

    @app.get("/test")
    async def get_test():
        return JSONResponse({"message": "GET success"})

    @app.get("/test_time")
    async def get_test_time():
        await asyncio.sleep(0.5)
        return JSONResponse({"message": "GET success"})

    @app.post("/test")
    async def post_test(request: Request):
        body = await request.json()
        return JSONResponse({"message": "POST success", "body": body})

    @app.get("/error")
    async def error_route():
        raise Exception("something went wrong")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    client = TestClient(app, raise_server_exceptions=False)

    yield {
        "monitor": monitor,
        "mock_server": mock_server,
        "client": client,
    }

    monitor.destroy()
    mock_server.stop_sync()


def test_get_homepage(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/")
    assert response.status_code == 200
    html = response.text
    assert "hello" in html

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/"
    assert event["status_code"] == 200
    assert event["response_body"] is not None
    assert "hello" in str(event["response_body"])


def test_get_test(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/test")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "GET success"

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/test"
    assert event["status_code"] == 200
    assert event["response_body"] is not None
    assert "GET success" in str(event["response_body"])


def test_post_test(fastapi_fixture):
    fx = fastapi_fixture

    body = {"name": "test"}
    response = fx["client"].post("/test", json=body)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "POST success"
    assert data["body"] == body

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "POST"
    assert event["endpoint"] == "/test"
    assert event["status_code"] == 200
    assert event["request_body"] == body
    assert event["response_body"] is not None
    assert "POST success" in str(event["response_body"])


def test_get_notfound(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/notfound")
    assert response.status_code == 404

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/notfound"
    assert event["status_code"] == 404


def test_get_error(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/error")
    assert response.status_code == 500

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/error"
    assert event["status_code"] == 500


def test_get_not_found(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/not_found")
    assert response.status_code == 404

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/not_found"
    assert event["status_code"] == 404


def test_request_headers_captured(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get(
        "/test",
        headers={"User-Agent": "test-client", "X-Custom-Header": "test-value"},
    )
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "request_headers" in event
    assert "user-agent" in event["request_headers"]
    assert "x-custom-header" in event["request_headers"]
    assert event["request_headers"]["x-custom-header"] == "test-value"


def test_response_headers_captured(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/test")
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "response_headers" in event
    assert "content-type" in event["response_headers"]
    assert event["response_headers"]["content-type"] == "application/json"


def test_duration_captured(fastapi_fixture):
    fx = fastapi_fixture

    response = fx["client"].get("/test_time")
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "duration_ms" in event
    assert isinstance(event["duration_ms"], int)
    assert event["duration_ms"] >= 500
