from flask.testing import *
from flask.testing import FlaskClient as OriginalFlaskClient, \
    FlaskCliRunner as OriginalFlaskCliRunner
from flask import _request_ctx_stack
from werkzeug.test import run_wsgi_app
from greenletio import async_


class FlaskClient(OriginalFlaskClient):
    def run_wsgi_app(self, environ, buffered=False):
        """Runs the wrapped WSGI app with the given environment.
        :meta private:
        """
        if self.cookie_jar is not None:
            self.cookie_jar.inject_wsgi(environ)

        rv = run_wsgi_app(self.application.wsgi_app, environ,
                          buffered=buffered)

        if self.cookie_jar is not None:
            self.cookie_jar.extract_wsgi(environ, rv[2])

        return rv

    async def get(self, *args, **kwargs):
        return await async_(super().get)(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return await async_(super().post)(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return await async_(super().put)(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await async_(super().patch)(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await async_(super().delete)(*args, **kwargs)

    async def head(self, *args, **kwargs):
        return await async_(super().head)(*args, **kwargs)

    async def options(self, *args, **kwargs):
        return await async_(super().options)(*args, **kwargs)

    async def trace(self, *args, **kwargs):
        return await async_(super().trace)(*args, **kwargs)

    async def __aenter__(self):
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        self.preserve_context = False

        # Normally the request context is preserved until the next
        # request in the same thread comes. When the client exits we
        # want to clean up earlier. Pop request contexts until the stack
        # is empty or a non-preserved one is found.
        while True:
            top = _request_ctx_stack.top

            if top is not None and top.preserved:
                await top.apop()
            else:
                break


class FlaskCliRunner(OriginalFlaskCliRunner):
    async def invoke(self, *args, **kwargs):
        return await async_(super().invoke)(*args, **kwargs)
