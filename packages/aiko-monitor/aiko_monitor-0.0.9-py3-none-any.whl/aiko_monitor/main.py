from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib

from .schema import SchemaUserConfig
from .send import SenderPool

project_root = Path(__file__).resolve().parents[2]
pyproject_path = project_root / "pyproject.toml"

pyproject = tomllib.loads(pyproject_path.read_text("utf-8"))
_AIKO_PKG_VERSION = pyproject.get("project").get("version")  # type: ignore
logger = logging.getLogger("aiko.monitor")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class Monitor:
    def __init__(
        self,
        app: Optional[Any] = None,
        *,
        project_key: str,
        secret_key: str,
        endpoint: Optional[str] = None,
        enabled: bool = True,
    ):
        self.cfg = SchemaUserConfig(
            project_key=project_key,
            secret_key=secret_key,
            endpoint=endpoint or "https://main.aikocorp.ai/api/monitor/ingest",
            enabled=enabled,
        )
        self._pool = SenderPool(
            cfg=self.cfg,
            workers=5,
            timeout_s=10.0,
            http2=False,
        )
        self._auto_instrument(app)

    def _auto_instrument(self, app) -> None:
        try:
            app_type = type(app).__name__
            module_name = type(app).__module__
            data = {"app_type": app_type, "module_name": module_name, "project_key": self.cfg.project_key}
            logger.debug("auto instrumenting", extra=data)

            if app_type == "FastAPI":
                from .integrations.fastapi import instrument

                instrument(self, app, _AIKO_PKG_VERSION)
            elif app_type == "Flask":
                from .integrations.flask import instrument

                instrument(self, app, _AIKO_PKG_VERSION)
            else:
                data = {"app_type": app_type, "module_name": module_name, "project_key": self.cfg.project_key}
                logger.error("unsupported app type", extra=data)
        except ImportError as e:
            logger.error(f"Missing integration: {e}")
        except Exception as e:
            logger.error(f"Instrumentation failed: {e}", exc_info=True)

    def add_event(self, event: Dict[str, Any]) -> None:
        if not self.cfg.enabled:
            return
        self._pool.submit(event)

    def destroy(self) -> None:
        self._pool.shutdown()
