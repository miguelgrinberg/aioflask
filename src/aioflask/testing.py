from flask.testing import FlaskClient as OriginalFlaskClient
from werkzeug.test import run_wsgi_app


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
