import asyncio
from functools import wraps
from inspect import iscoroutinefunction
import os
from flask import Flask as OriginalFlask
from flask.globals import _app_ctx_stack, _request_ctx_stack
from greenletio import await_
from .asgi import WsgiToAsgiInstance


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
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app)

    async def asgi_app(self, scope, receive, send):
        if not self.async_fixed:
            self._fix_async()
        return await WsgiToAsgiInstance(self.wsgi_app)(scope, receive, send)

    async def __call__(self, scope, receive, send):
        return await self.asgi_app(scope, receive, send)
