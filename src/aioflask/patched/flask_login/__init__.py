from functools import wraps
from werkzeug.local import LocalProxy
from aioflask import current_app, g
from flask import _request_ctx_stack
from aioflask.patch import patch_decorator, patch_decorator_method
import flask_login
from flask_login import login_required, fresh_login_required, LoginManager

for symbol in flask_login.__all__:
    try:
        globals()[symbol] = getattr(flask_login, symbol)
    except AttributeError:
        pass

# the decorators that register callbacks need to be patched to support async
# functions
LoginManager.user_loader = patch_decorator_method(
    LoginManager, 'user_loader')
LoginManager.header_loader = patch_decorator_method(
    LoginManager, 'header_loader')
LoginManager.request_loader = patch_decorator_method(
    LoginManager, 'request_loader')
LoginManager.unauthorized_handler = patch_decorator_method(
    LoginManager, 'unauthorized_handler')
LoginManager.needs_refresh_handler = patch_decorator_method(
    LoginManager, 'needs_refresh_handler')

# The current_user context local is implemented in a way that creates some
# complications for aioflask:
# 1. It can cause the user loader callback to be called at a random time in the
#    life of the request. Since the user loader can now be async, it might need
#    to be awaited, but doing (await current_user) would be really weird.
# 2. It caches the retrieved user in a custom property of the request context,
#    which Flask ignores when making request context copies.
#
# To address #1, the login_requred and fresh_login_required are modified to
# load the user and cache it, before the view function is called.
# To address #2, the current_user context local is modified to cache the user
# in the g object.

original_login_required = patch_decorator(login_required)
original_fresh_login_required = patch_decorator(fresh_login_required)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        current_app.login_manager._load_user()
        g.flask_login_current_user = _request_ctx_stack.top.user
        return original_login_required(f)(*args, **kwargs)

    return wrapper


def fresh_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        LoginManager._load_user()
        g.flask_login_current_user = current_user._get_current_object()
        return original_fresh_login_required(f)(*args, **kwargs)

    return wrapper


current_user = LocalProxy(lambda: g.flask_login_current_user)
