import sys
from greenletio import async_
from flask.ctx import *
from flask.ctx import AppContext as OriginalAppContext, _sentinel, \
    _app_ctx_stack, appcontext_popped


class AppContext(OriginalAppContext):
    async def apush(self):
        """Binds the app context to the current context."""
        self.push()

    async def apop(self, exc=_sentinel):
        """Pops the app context."""
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]

                @async_
                def do_teardown_async():
                    _app_ctx_stack.push(self)
                    print(4, self.app)
                    self.app.do_teardown_appcontext(exc)
                    print(6)
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
