from aioflask.patch import patch_decorator, patch_decorator_method
import flask_login

for symbol in flask_login.__all__:
    try:
        globals()[symbol] = getattr(flask_login, symbol)
    except AttributeError:
        pass

login_required = patch_decorator(login_required)  # noqa: F821
LoginManager.user_loader = patch_decorator_method(  # noqa: F821
    LoginManager, 'user_loader')  # noqa: F821
