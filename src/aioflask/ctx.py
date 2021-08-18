import sys
from greenletio import async_
from flask.ctx import *
from flask.ctx import AppContext as OriginalAppContext, \
    RequestContext as OriginalRequestContext, _sentinel, _app_ctx_stack, \
    _request_ctx_stack, appcontext_popped


class AppContext(OriginalAppContext):
    async def apush(self):
        """Binds the app context to the current context."""
        self.push()

    async def apop(self, exc=_sentinel):
        """Pops the app context."""
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:  # pragma: no cover
                    exc = sys.exc_info()[1]

                @async_
                def do_teardown_async():
                    _app_ctx_stack.push(self)
                    self.app.do_teardown_appcontext(exc)
                    _app_ctx_stack.pop()

                await do_teardown_async()
        finally:
            rv = _app_ctx_stack.pop()
        assert rv is self, \
            f"Popped wrong app context.  ({rv!r} instead of {self!r})"
        appcontext_popped.send(self.app)

    async def __aenter__(self):
        await self.apush()
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.apop(exc_value)


class RequestContext(OriginalRequestContext):
    async def apush(self):
        self.push()

    async def apop(self, exc=_sentinel):
        app_ctx = self._implicit_app_ctx_stack.pop()
        clear_request = False

        try:
            if not self._implicit_app_ctx_stack:
                self.preserved = False
                self._preserved_exc = None
                if exc is _sentinel:  # pragma: no cover
                    exc = sys.exc_info()[1]

                @async_
                def do_teardown():
                    _request_ctx_stack.push(self)
                    self.app.do_teardown_request(exc)
                    _request_ctx_stack.pop()

                await do_teardown()

                request_close = getattr(self.request, "close", None)
                if request_close is not None:  # pragma: no branch
                    request_close()
                clear_request = True
        finally:
            rv = _request_ctx_stack.pop()

            # get rid of circular dependencies at the end of the request
            # so that we don't require the GC to be active.
            if clear_request:
                rv.request.environ["werkzeug.request"] = None

            # Get rid of the app as well if necessary.
            if app_ctx is not None:
                await app_ctx.apop(exc)

            assert (
                rv is self
            ), f"Popped wrong request context. ({rv!r} instead of {self!r})"

    async def aauto_pop(self, exc):
        if self.request.environ.get("flask._preserve_context") or (
            exc is not None and self.app.preserve_context_on_exception
        ):  # pragma: no cover
            self.preserved = True
            self._preserved_exc = exc
        else:
            await self.apop(exc)

    async def __aenter__(self):
        await self.apush()
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.aauto_pop(exc_value)
