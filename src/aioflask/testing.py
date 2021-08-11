from flask.testing import *
from flask.testing import FlaskClient as OriginalFlaskClient, \
    FlaskCliRunner as OriginalFlaskCliRunner
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


class FlaskCliRunner(OriginalFlaskCliRunner):
    async def invoke(self, *args, **kwargs):
        return await async_(super().invoke)(*args, **kwargs)
