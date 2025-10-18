from __future__ import annotations

import queue
import random
import threading
import time
from typing import Any, Dict

import httpx

from .core import b64url_decode, gzip_event, redact_event, sign
from .schema import SchemaUserConfig


class SenderPool:
    def __init__(
        self,
        *,
        cfg: SchemaUserConfig,
        workers: int = 16,
        max_queue: int = 5000,
        retry_count: int = 3,
        timeout_s: float = 5.0,
        http2: bool = False,
    ):
        self.cfg = cfg
        self._secret = b64url_decode(self.cfg.secret_key)
        self.retry_count = retry_count
        self.timeout_s = timeout_s

        self.q: queue.Queue[Dict[str, Any]] = queue.Queue(maxsize=max_queue)
        self.stop = threading.Event()

        self.threads = [
            threading.Thread(target=self._worker, name=f"sender-{i}", daemon=True, args=(http2,))
            for i in range(workers)
        ]
        for t in self.threads:
            t.start()

    def submit(self, event: Dict[str, Any]) -> None:
        self.q.put(event, block=True)

    def shutdown(self) -> None:
        self.stop.set()
        self.q.join()
        for t in self.threads:
            t.join(timeout=2)

    def _new_client(self, http2: bool) -> httpx.Client:
        return httpx.Client(
            http2=http2,
            timeout=httpx.Timeout(self.timeout_s),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=100),
        )

    def _worker(self, http2: bool) -> None:
        client = self._new_client(http2=http2)
        while not self.stop.is_set():
            try:
                event = self.q.get(timeout=0.2)
            except queue.Empty:
                continue

            ok = self._send(client, event)
            if ok:
                self.q.task_done()

    def _send(self, client: httpx.Client, event: Dict[str, Any]) -> bool:
        body = gzip_event(redact_event(event))
        sig = sign(self._secret, body)
        headers = {
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "X-Project-Key": self.cfg.project_key,
            "X-Signature": sig,
        }
        backoff = 0.25
        for attempt in range(self.retry_count + 1):
            try:
                r = client.post(self.cfg.endpoint, content=body, headers=headers)
                if r.is_success:
                    return True
                if r.status_code not in (408, 429) and not (500 <= r.status_code < 600):
                    return False
            except (httpx.TimeoutException, httpx.TransportError):
                pass
            if attempt < self.retry_count:
                time.sleep(backoff * (0.8 + 0.4 * random.random()))
                backoff = min(backoff * 2, 2.0)
        return False
