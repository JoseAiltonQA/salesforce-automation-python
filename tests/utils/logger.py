import json
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import allure

LEVELS = ["debug", "info", "warn", "error"]
MASK_KEYS = {"password", "passwd", "token", "authorization", "cookie", "set-cookie", "sf_token", "session"}
MAX_PREVIEW_CHARS = int(os.environ.get("LOG_MAX_PREVIEW", "4000"))


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _mask(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {k: ("***" if k.lower() in MASK_KEYS else _mask(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mask(v) for v in value]
    if isinstance(value, str):
        if len(value) > 3 and any(k in value.lower() for k in MASK_KEYS):
            return "***"
        return value[:MAX_PREVIEW_CHARS]
    return value


class TestLogger:
    def __init__(self, test_id: str, level: str = "info") -> None:
        self.test_id = test_id
        self.level = level
        self.buffer: List[Dict[str, Any]] = []
        self.global_buffer: List[str] = []
        self.step_buffers: Dict[str, List[str]] = {}
        self.step_stack: List[str] = []
        self._attached = False

    def _should_log(self, level: str) -> bool:
        return LEVELS.index(level) >= LEVELS.index(self.level)

    def _push(self, level: str, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        if not self._should_log(level):
            return
        entry = {
            "ts": _iso_now(),
            "level": level.upper(),
            "test": self.test_id,
            "message": msg,
        }
        if meta:
            entry["meta"] = _mask(meta)
        line = f"{entry['ts']} | {entry['level']} | run_id={self.test_id} | step={self.current_step or '-'} | {msg}"
        if meta:
            line += " " + json.dumps(entry["meta"], ensure_ascii=False)
        print(line, flush=True)

        if self.current_step:
            self.step_buffers.setdefault(self.current_step, []).append(line)
        else:
            self.global_buffer.append(line)
        self.buffer.append(entry)

    def debug(self, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._push("debug", msg, meta)

    def info(self, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._push("info", msg, meta)

    def warn(self, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._push("warn", msg, meta)

    def error(self, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._push("error", msg, meta)

    def step(self, msg: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.info(f"[STEP] {msg}", meta)

    def attach_once(self, name: str = "execution.log") -> None:
        if self._attached:
            return
        text = "\n".join(self.global_buffer or [])
        if text:
            allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)
        self._attached = True

    @property
    def current_step(self) -> Optional[str]:
        return self.step_stack[-1] if self.step_stack else None

    def enter_step(self, name: str) -> None:
        self.step_stack.append(name)
        self.step_buffers.setdefault(name, [])

    def exit_step(self, name: str) -> None:
        if self.step_stack and self.step_stack[-1] == name:
            self.step_stack.pop()
        buf = self.step_buffers.get(name, [])
        if buf:
            allure.attach("\n".join(buf), name="Logs", attachment_type=allure.attachment_type.TEXT)
            self.step_buffers[name] = []


def setup_page_listeners(page, log: TestLogger) -> None:
    # Console messages from the page
    def on_console(msg):
        txt = msg.text
        if "[STEP]" in txt or "[LOG]" in txt:
            return
        log.info("console", {"type": msg.type, "text": txt})

    page.on("console", on_console)

    # Request failures
    page.on(
        "requestfailed",
        lambda req: log.warn(
            "requestfailed",
            {"url": req.url, "method": req.method, "failure": req.failure},
        ),
    )

    # Responses with error status
    page.on(
        "response",
        lambda res: res.status >= 400
        and log.warn(
            "response",
            {"url": res.url, "status": res.status, "statusText": res.status_text},
        ),
    )

    # Page errors
    page.on("pageerror", lambda exc: log.error("pageerror", {"error": str(exc)}))

    # Navigations
    page.on("framenavigated", lambda f: log.info("navigated", {"url": f.url}))


def create_logger_for_test(test_id: str) -> TestLogger:
    level = os.environ.get("LOG_LEVEL", "info").lower()
    if level not in LEVELS:
        level = "info"
    return TestLogger(test_id=test_id, level=level)


@contextmanager
def step(logger: TestLogger, name: str):
    with allure.step(name):
        logger.enter_step(name)
        try:
            yield logger
        finally:
            logger.exit_step(name)
