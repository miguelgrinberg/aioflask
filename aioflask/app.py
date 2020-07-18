import asyncio
from functools import wraps
from inspect import iscoroutinefunction
import os
from flask import Flask as OriginalFlask, cli
from flask.globals import _app_ctx_stack, _request_ctx_stack
from flask.helpers import get_debug_flag, get_env, get_load_dotenv
from greenletio import await_
import uvicorn
from .asgi import WsgiToAsgiInstance
from .cli import show_server_banner


def async_get_ident():
    return asyncio.current_task()


class Flask(OriginalFlask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.async_fixed = False

    def async_to_sync(self, coro):
        if not iscoroutinefunction(coro):
            return coro

        @wraps(coro)
        def decorated(*args, **kwargs):
            reqctx = _request_ctx_stack.top.copy()

            @await_
            async def _coro():
                with reqctx:
                    return await coro(*args, **kwargs)

            return _coro()

        return decorated

    def _fix_async(self):
        self.async_fixed = True

        _app_ctx_stack.__ident_func__ = async_get_ident
        _request_ctx_stack.__ident_func__ = async_get_ident

        self.view_functions = {
            name: self.async_to_sync(func)
            for name, func in self.view_functions.items()
        }
        for key in self.error_handler_spec:
            for code in self.error_handler_spec[key]:
                self.error_handler_spec[key][code] = {
                    exc_class: self.async_to_sync(func)
                    for exc_class, func in
                    self.error_handler_spec[key][code].items()
                }
        for key in self.before_request_funcs:
            self.before_request_funcs[key] = [
                self.async_to_sync(func)
                for func in self.before_request_funcs[key]
            ]
        self.before_first_request_funcs = [
            self.async_to_sync(func)
            for func in self.before_first_request_funcs
        ]
        for key in self.after_request_funcs:
            self.after_request_funcs[key] = [
                self.async_to_sync(func)
                for func in self.after_request_funcs[key]
            ]
        for key in self.teardown_request_funcs:
            self.teardown_request_funcs[key] = [
                self.async_to_sync(func)
                for func in self.teardown_request_funcs[key]
            ]
        self.teardown_appcontext_funcs = [
            self.async_to_sync(func)
            for func in self.teardown_appcontext_funcs
        ]

        if os.environ.get('AIOFLASK_USE_DEBUGGER') == 'true':
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app, evalex=True)

    async def asgi_app(self, scope, receive, send):
        if not self.async_fixed:
            self._fix_async()
        return await WsgiToAsgiInstance(self.wsgi_app)(scope, receive, send)

    async def __call__(self, scope, receive, send):
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
            workers=1,
            log_level='debug' if self.debug else 'info',
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
        )
