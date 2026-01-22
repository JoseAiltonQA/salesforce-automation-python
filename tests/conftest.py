import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import allure
import httpx
import pytest
from playwright.sync_api import Page
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import get_settings  # noqa: E402

ARTIFACT_ROOT = Path("test-results")
SCREENSHOT_DIR = ARTIFACT_ROOT / "screenshots"
TRACE_DIR = ARTIFACT_ROOT / "traces"
VIDEO_DIR = ARTIFACT_ROOT / "videos"
REPORTS_DIR = Path("reports")
API_LOG_DIR = REPORTS_DIR / "api-logs"

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "sf_token"}
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "token",
    "authorization",
    "cookie",
    "set-cookie",
    "sf_token",
    "session",
    "secret",
    "api_key",
    "apikey",
    "refresh",
    "client_secret",
}
PII_PATTERNS = {
    "email": re.compile(r"[\w\.-]+@[\w\.-]+\.\w+", re.IGNORECASE),
    "phone": re.compile(r"\+?\d{0,3}\s*\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}"),
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
}
CORRELATION_HEADERS = ("x-correlation-id", "x-request-id", "traceparent", "x-amzn-trace-id")
MAX_PREVIEW_CHARS = 4000
API_METRICS: List[Dict[str, Any]] = []


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value)


def _safe_git_cmd(args: List[str]) -> str:
    try:
        return (
            subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True)
            .strip()
        )
    except Exception:
        return ""


def _mask_text(value: str) -> str:
    masked = value
    for pattern in PII_PATTERNS.values():
        masked = pattern.sub("[redacted]", masked)
    return masked


def _sanitize_body(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, (bool, int, float)):
        return data
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    if isinstance(data, str):
        return _mask_text(data)[:MAX_PREVIEW_CHARS]
    if isinstance(data, dict):
        return {
            key: "[redacted]" if key.lower() in SENSITIVE_KEYS else _sanitize_body(value)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_sanitize_body(item) for item in data]
    return _mask_text(str(data))[:MAX_PREVIEW_CHARS]


def _sanitize_headers(headers: httpx._types.HeaderTypes) -> Dict[str, str]:
    clean: Dict[str, str] = {}
    for key, value in headers.items():
        key_lower = str(key).lower()
        if key_lower in SENSITIVE_HEADERS:
            clean[str(key)] = "[redacted]"
        else:
            clean[str(key)] = _mask_text(str(value))
    return clean


def _extract_correlation_id(headers: Dict[str, str]) -> str:
    for header in CORRELATION_HEADERS:
        if headers.get(header):
            return f"{header}: {headers[header]}"
    return ""


def _percentile(values: List[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * percentile
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[int(k)]
    return values_sorted[f] + (values_sorted[c] - values_sorted[f]) * (k - f)


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session", autouse=True)
def _prepare_artifact_dirs():
    for directory in (
        ARTIFACT_ROOT,
        SCREENSHOT_DIR,
        TRACE_DIR,
        VIDEO_DIR,
        REPORTS_DIR,
        API_LOG_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def allure_environment(browser_name, settings):
    env_dir = Path("allure-results")
    env_dir.mkdir(parents=True, exist_ok=True)

    branch = _safe_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
    commit = _safe_git_cmd(["rev-parse", "--short", "HEAD"])

    entries = [
        ("os", platform.platform()),
        ("browser", browser_name),
        ("headless", str(settings.headless)),
    ]
    if branch:
        entries.append(("branch", branch))
    if commit:
        entries.append(("commit", commit))

    env_file = env_dir / "environment.properties"
    with env_file.open("w", encoding="utf-8") as file:
        for key, value in entries:
            file.write(f"{key}={value}\n")


@pytest.fixture()
def api_client(settings, request):
    if not settings.sf_api_base_url or not settings.sf_token:
        pytest.skip("Defina SF_API_BASE_URL e SF_TOKEN no .env para rodar testes de API.")

    test_id = request.node.nodeid
    events: List[Dict[str, Any]] = []

    default_headers = {
        "Authorization": f"Bearer {settings.sf_token}",
        "Content-Type": "application/json",
    }

    def _on_request(req: httpx.Request):
        req.extensions["start_time"] = time.perf_counter()
        events.append(
            {
                "type": "request",
                "test": test_id,
                "method": req.method,
                "url": str(req.url),
                "headers": _sanitize_headers(req.headers),
                "body": _sanitize_body(req.content),
            }
        )

    def _on_response(res: httpx.Response):
        start = res.request.extensions.get("start_time")
        elapsed_ms = (time.perf_counter() - start) * 1000 if start else None

        try:
            body = res.json()
        except Exception:
            body = res.text

        sanitized_headers = _sanitize_headers(res.headers)
        correlation = _extract_correlation_id({k.lower(): v for k, v in res.headers.items()})
        sanitized_body = _sanitize_body(body)
        size_bytes = len(res.content or b"")

        event = {
            "type": "response",
            "test": test_id,
            "method": res.request.method,
            "url": str(res.request.url),
            "status": res.status_code,
            "elapsed_ms": round(elapsed_ms, 2) if elapsed_ms else None,
            "headers": sanitized_headers,
            "body": sanitized_body,
            "size_bytes": size_bytes,
        }
        if correlation:
            event["correlation_id"] = correlation

        events.append(event)
        API_METRICS.append(
            {
                "test": test_id,
                "endpoint": res.request.url.path,
                "method": res.request.method,
                "status": res.status_code,
                "elapsed_ms": elapsed_ms or 0.0,
                "ok": res.is_success,
                "size_bytes": size_bytes,
                "correlation_id": correlation,
            }
        )

    client = httpx.Client(
        base_url=settings.sf_api_base_url,
        headers=default_headers,
        timeout=30.0,
        event_hooks={"request": [_on_request], "response": [_on_response]},
    )
    request.node.api_events = events

    yield client

    client.close()
    if events:
        log_file = API_LOG_DIR / f"{_slugify(test_id)}.json"
        log_file.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, settings):
    launch_args = dict(browser_type_launch_args)
    launch_args.setdefault("headless", settings.headless)
    return launch_args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "record_video_dir": str(VIDEO_DIR)}


@pytest.fixture()
def context(browser, browser_context_args, request):
    context = browser.new_context(**browser_context_args)
    yield context

    recorded_videos = [page.video for page in context.pages if page.video]
    context.close()

    for index, video in enumerate(recorded_videos, start=1):
        try:
            video_path = Path(video.path())
        except Exception:
            continue

        if video_path.exists():
            allure.attach.file(
                str(video_path),
                name=f"video-{index}",
                attachment_type=allure.attachment_type.WEBM,
            )


@pytest.fixture()
def page(context, request) -> Page:
    test_slug = _slugify(request.node.nodeid)
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    yield page

    trace_path = TRACE_DIR / f"{test_slug}.zip"
    try:
        context.tracing.stop(path=str(trace_path))
    except Exception:
        trace_path = None

    if trace_path and trace_path.exists():
        allure.attach.file(
            str(trace_path),
            name="trace",
            attachment_type=allure.attachment_type.ZIP,
        )


def _summarize_api_events(events: List[Dict[str, Any]]) -> str:
    responses = [evt for evt in events if evt["type"] == "response"]
    if not responses:
        return "Sem respostas registradas."
    last = responses[-1]
    parts = [
        f"Metodo: {last.get('method')}",
        f"URL: {last.get('url')}",
        f"Status: {last.get('status')}",
        f"Tempo (ms): {last.get('elapsed_ms')}",
        f"Tamanho (bytes): {last.get('size_bytes')}",
    ]
    if last.get("correlation_id"):
        parts.append(f"Correlation: {last['correlation_id']}")
    return "\n".join(parts)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when != "call":
        return

    events = getattr(item, "api_events", None)
    if events:
        allure.attach(
            json.dumps(events, ensure_ascii=False, indent=2),
            name="api-request-response",
            attachment_type=allure.attachment_type.JSON,
        )
        allure.attach(
            _summarize_api_events(events),
            name="api-summary",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if not API_METRICS:
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_file = REPORTS_DIR / "api-metrics.json"

    total = len(API_METRICS)
    success = sum(1 for m in API_METRICS if 200 <= m["status"] < 400)
    fail = total - success

    by_endpoint: Dict[str, Dict[str, Any]] = {}
    for metric in API_METRICS:
        key = f"{metric['method']} {metric['endpoint']}"
        by_endpoint.setdefault(key, {"times": [], "statuses": []})
        by_endpoint[key]["times"].append(metric["elapsed_ms"])
        by_endpoint[key]["statuses"].append(metric["status"])

    endpoint_summaries = []
    for endpoint, data in by_endpoint.items():
        endpoint_summaries.append(
            {
                "endpoint": endpoint,
                "count": len(data["times"]),
                "avg_ms": round(sum(data["times"]) / len(data["times"]), 2),
                "p95_ms": round(_percentile(data["times"], 0.95) or 0, 2),
                "min_ms": round(min(data["times"]), 2),
                "max_ms": round(max(data["times"]), 2),
            }
        )

    summary = {
        "total_requests": total,
        "success": success,
        "failed": fail,
        "success_rate": round((success / total) * 100, 2) if total else 0,
        "by_endpoint": endpoint_summaries,
    }

    metrics_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    txt_summary_lines = [
        f"Total: {total}",
        f"Sucesso: {success}",
        f"Falha: {fail}",
        f"Taxa de sucesso: {summary['success_rate']}%",
    ]
    report_txt = REPORTS_DIR / "api-metrics.txt"
    report_txt.write_text("\n".join(txt_summary_lines), encoding="utf-8")


@pytest.fixture()
def selenium_driver(settings):
    options = Options()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()
