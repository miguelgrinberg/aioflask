import asyncio
from functools import wraps
from inspect import iscoroutinefunction
import os
from flask import Flask as OriginalFlask, cli
from flask.globals import _app_ctx_stack, _request_ctx_stack
from flask.helpers import get_debug_flag, get_env, get_load_dotenv
from greenletio import await_, async_
import uvicorn
from .asgi import WsgiToAsgiInstance
from .cli import show_server_banner, AppGroup
from .testing import FlaskClient


class Flask(OriginalFlask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cli = AppGroup()
        self.jinja_options['enable_async'] = True
        self.test_client_class = FlaskClient
        self.async_fixed = False

    def ensure_sync(self, func):
        if not iscoroutinefunction(func):
            return func

        @wraps(func)
        def decorated(*args, **kwargs):
            reqctx = _request_ctx_stack.top.copy()

            async def _coro():
                with reqctx:
                    return await func(*args, **kwargs)

            return await_(_coro())

        return decorated

    def _fix_async(self):  # pragma: no cover
        self.async_fixed = True

        if os.environ.get('AIOFLASK_USE_DEBUGGER') == 'true':
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app, evalex=True)

    async def asgi_app(self, scope, receive, send):  # pragma: no cover
        if not self.async_fixed:
            self._fix_async()
        return await WsgiToAsgiInstance(self.wsgi_app)(scope, receive, send)

    async def __call__(self, scope, receive, send=None):  # pragma: no cover
        if send is None:
            # we were called with two arguments, so this is likely a WSGI app
            raise RuntimeError('The WSGI interface is not supported by '
                               'aioflask, use an ASGI web server instead.')
        return await self.asgi_app(scope, receive, send)

    def run(self, host=None, port=None, debug=None, load_dotenv=True,
            **options):

        if get_load_dotenv(load_dotenv):
            cli.load_dotenv()

            # if set, let env vars override previous values
            if "FLASK_ENV" in os.environ:
                self.env = get_env()
                self.debug = get_debug_flag()
            elif "FLASK_DEBUG" in os.environ:
                self.debug = get_debug_flag()

        # debug passed to method overrides all other sources
        if debug is not None:
            self.debug = bool(debug)

        server_name = self.config.get("SERVER_NAME")
        sn_host = sn_port = None

        if server_name:
            sn_host, _, sn_port = server_name.partition(":")

        if not host:
            if sn_host:
                host = sn_host
            else:
                host = "127.0.0.1"

        if port or port == 0:
            port = int(port)
        elif sn_port:
            port = int(sn_port)
        else:
            port = 5000

        options.setdefault("use_reloader", self.debug)
        options.setdefault("use_debugger", self.debug)
        options.setdefault("threaded", True)
        options.setdefault("workers", 1)

        certfile = None
        keyfile = None
        cert = options.get('ssl_context')
        if cert is not None and len(cert) == 2:
            certfile = cert[0]
            keyfile = cert[1]
        elif cert == 'adhoc':
            raise RuntimeError(
                'Aad-hoc certificates are not supported by aioflask.')

        if debug:
            os.environ['FLASK_DEBUG'] = 'true'

        if options['use_debugger']:
            os.environ['AIOFLASK_USE_DEBUGGER'] = 'true'

        show_server_banner(self.env, self.debug, self.name, False)

        uvicorn.run(
            self.import_name + ':app',
            host=host,
            port=port,
            reload=options['use_reloader'],
            workers=options['workers'],
            log_level='debug' if self.debug else 'info',
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
        )
