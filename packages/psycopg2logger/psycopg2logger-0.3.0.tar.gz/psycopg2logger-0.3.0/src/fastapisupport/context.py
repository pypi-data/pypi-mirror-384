from contextvars import ContextVar

current_request_path = ContextVar("current_request_path", default=None)
current_request_method = ContextVar("current_request_method", default=None)
log_port = ContextVar("log_port", default=6000)
