import json
import time

import pytest
from flask import Flask, jsonify, request

from src.aiko_monitor.main import Monitor
from tests.mock_server import MockMonitorServer, wait_for


@pytest.fixture
def flask_fixture():
    secret = "aNlvpEIXkeEubNgikWXyGnh8LyXa72yZhR9lEmzgHCM"
    project_key = "pk_92Yb_kCIwRhy06UF-FQShg"

    mock_server = MockMonitorServer(port=0, secret=secret, project_key=project_key)
    mock_server.start_sync()

    app = Flask(__name__)

    monitor = Monitor(
        app,
        project_key=project_key,
        secret_key=secret,
        endpoint=f"http://localhost:{mock_server.port}/api/monitor/ingest",
        enabled=True,
    )

    @app.route("/")
    def home():
        return "<html><body><h1>hello</h1></body></html>"

    @app.route("/test")
    def get_test():
        return jsonify({"message": "GET success"})

    @app.route("/test_time")
    def get_test_time():
        time.sleep(0.5)
        return jsonify({"message": "GET success"})

    @app.route("/test", methods=["POST"])
    def post_test():
        return jsonify({"message": "POST success", "body": request.json})

    @app.route("/error")
    def error_route():
        raise Exception("something went wrong")

    client = app.test_client()

    yield {
        "monitor": monitor,
        "mock_server": mock_server,
        "client": client,
    }

    monitor.destroy()
    mock_server.stop_sync()


def test_get_homepage(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "hello" in html

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/"
    assert event["status_code"] == 200
    assert event["response_body"] is not None
    assert "hello" in str(event["response_body"])


def test_get_test(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/test")
    assert response.status_code == 200

    data = response.get_json()
    assert data["message"] == "GET success"

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/test"
    assert event["status_code"] == 200
    assert event["response_body"] is not None
    assert "GET success" in str(event["response_body"])


def test_post_test(flask_fixture):
    fx = flask_fixture

    body = {"name": "test"}
    response = fx["client"].post("/test", data=json.dumps(body), content_type="application/json")
    assert response.status_code == 200

    data = response.get_json()
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


def test_get_notfound(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/notfound")
    assert response.status_code == 404

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/notfound"
    assert event["status_code"] == 404


def test_get_error(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/error")
    assert response.status_code == 500

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/error"
    assert event["status_code"] == 500


def test_get_not_found(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/not_found")
    assert response.status_code == 404

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert event["method"] == "GET"
    assert event["endpoint"] == "/not_found"
    assert event["status_code"] == 404


def test_request_headers_captured(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/test", headers={"User-Agent": "test-client", "X-Custom-Header": "test-value"})
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "request_headers" in event
    assert "user-agent" in event["request_headers"]
    assert "x-custom-header" in event["request_headers"]
    assert event["request_headers"]["x-custom-header"] == "test-value"


def test_response_headers_captured(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/test")
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "response_headers" in event
    assert "content-type" in event["response_headers"]
    assert event["response_headers"]["content-type"] == "application/json"


def test_duration_captured(flask_fixture):
    fx = flask_fixture

    response = fx["client"].get("/test_time")
    assert response.status_code == 200

    assert wait_for(lambda: len(fx["mock_server"].received_events) > 0, timeout=3.0)

    event = fx["mock_server"].received_events[0]
    assert "duration_ms" in event
    assert isinstance(event["duration_ms"], int)
    assert event["duration_ms"] >= 500
