from functools import wraps
import sys
from werkzeug.local import LocalProxy
from aioflask import current_app, g
from flask import _request_ctx_stack
from aioflask.patch import patch_decorator, patch_decorator_method
import flask_login
from flask_login import login_required, fresh_login_required, \
    LoginManager as OriginalLoginManager

for symbol in flask_login.__all__:
    try:
        globals()[symbol] = getattr(flask_login, symbol)
    except AttributeError:
        pass


def _user_context_processor():
    return {'current_user': _get_user()}


def _load_user():
    # Obtain the current user and preserve it in the g object. Flask-Login
    # saves the user in a custom attribute of the request context, but that
    # doesn't work with aioflask because when a copy of the request context is
    # made, custom attributes are not carried over to the copy.
    current_app.login_manager._load_user()
    g.flask_login_current_user = _request_ctx_stack.top.user


def _get_user():
    # Return the current user. This function is linked to the current_user
    # context local, but unlike the original in Flask-Login, it does not
    # attempt to load the user, it just returns the user that was pre-loaded.
    # This avoids the somewhat tricky complication of triggering database
    # operations that need to be awaited, which would require using something
    # like (await current_user)
    if hasattr(g, 'flask_login_current_user'):
        return g.flask_login_current_user
    return current_app.login_manager.anonymous_user()


class LoginManager(OriginalLoginManager):
    def init_app(self, app, add_context_processor=True):
        super().init_app(app, add_context_processor=False)
        if add_context_processor:
            app.context_processor(_user_context_processor)

        # To prevent the current_user context local from triggering I/O at a
        # random time when it is first referenced (which is a big complication
        # if the I/O is async and needs to be awaited), we force the user to be
        # loaded before each request. This isn't a perfect solution, because
        # a before request handler registered before this one will not see the
        # current user.
        app.before_request(_load_user)

    # the decorators that register callbacks need to be patched to support
    # async views
    user_loader = patch_decorator_method(OriginalLoginManager, 'user_loader')
    header_loader = patch_decorator_method(
        OriginalLoginManager, 'header_loader')
    request_loader = patch_decorator_method(
        OriginalLoginManager, 'request_loader')
    unauthorized_handler = patch_decorator_method(
        OriginalLoginManager, 'unauthorized_handler')
    needs_refresh_handler = patch_decorator_method(
        OriginalLoginManager, 'needs_refresh_handler')


# patch the two login_required decorators so that they accept async views
login_required = patch_decorator(login_required)
fresh_login_required = patch_decorator(fresh_login_required)


# redefine the current_user context local
current_user = LocalProxy(_get_user)

# patch the _get_user() function in the flask_login.utils module so that any
# calls to get current_user in Flask-Login functions are redirected here
setattr(sys.modules['flask_login.utils'], '_get_user', _get_user)
