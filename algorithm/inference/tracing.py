"""W3C traceparent 解析 + logging 注入.

如果未来接入完整 OpenTelemetry, 把这个文件换成
`opentelemetry-instrumentation-fastapi` 的初始化即可.
本期只做最小: 从 inbound HTTP header 里把 traceparent 抽出来,
塞进 contextvars, 让 logger 输出时带上 trace_id / span_id.
"""
from __future__ import annotations

import contextvars
import logging
import re
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[0-9a-f]{2})-"
    r"(?P<trace_id>[0-9a-f]{32})-"
    r"(?P<span_id>[0-9a-f]{16})-"
    r"(?P<flags>[0-9a-f]{2})$"
)

trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")
span_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="-")
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def parse_traceparent(value: Optional[str]) -> tuple[str, str]:
    if not value:
        return "-", "-"
    m = _TRACEPARENT_RE.match(value.strip())
    if not m:
        return "-", "-"
    return m.group("trace_id"), m.group("span_id")


class TraceContextMiddleware(BaseHTTPMiddleware):
    """每个请求把 traceparent + body.requestId 写进 contextvars."""

    async def dispatch(self, request: Request, call_next) -> Response:
        traceparent = request.headers.get("traceparent")
        trace_id, span_id = parse_traceparent(traceparent)
        # requestId 由 body 里给, 这里先用 url 兜底
        req_id = request.headers.get("x-request-id", "-")

        tid_tok = trace_id_ctx.set(trace_id)
        sid_tok = span_id_ctx.set(span_id)
        rid_tok = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["x-trace-id"] = trace_id
            return response
        finally:
            trace_id_ctx.reset(tid_tok)
            span_id_ctx.reset(sid_tok)
            request_id_ctx.reset(rid_tok)


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_ctx.get()
        record.span_id = span_id_ctx.get()
        record.request_id = request_id_ctx.get()
        return True


def install_logging() -> None:
    fmt = "%(asctime)s %(levelname)s trace=%(trace_id)s span=%(span_id)s req=%(request_id)s %(name)s %(message)s"
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(TraceContextFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
