from typing import Awaitable, Callable
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapisupport.context import (
    current_request_path,
    current_request_method,
    log_port,
)
import psycopg2logger


class Psycopg2InterceptorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_port=6000):
        super().__init__(app)
        self.log_port = log_port

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ):
        log_port.set(self.log_port)
        path_token = current_request_path.set(request.url.path)
        http_method = current_request_method.set(request.method)
        try:
            response = await call_next(request)
        finally:
            current_request_path.reset(path_token)
            current_request_method.reset(http_method)
        return response
