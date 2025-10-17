import functools
import psycopg2

from psycopg2logger.cursorinterceptor import CursorInterceptor, InterceptingConnection

_psycopg2_connect = psycopg2.connect


@functools.wraps(_psycopg2_connect)
def connect_intercepting(*args, **kwargs):
    kwargs.setdefault("connection_factory", InterceptingConnection)
    return _psycopg2_connect(*args, **kwargs)


psycopg2.connect = connect_intercepting
