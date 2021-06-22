from functools import wraps
from aioflask import current_app


def patch_decorator(decorator):
    def patched_decorator(f):
        @wraps(f)
        def ensure_sync(*a, **kw):
            return current_app.ensure_sync(f)(*a, **kw)

        return decorator(ensure_sync)
    return patched_decorator


def patch_decorator_with_args(decorator):
    def patched_decorator(*args, **kwargs):
        def inner_patched_decorator(f):
            @wraps(f)
            def ensure_sync(*a, **kw):
                return current_app.ensure_sync(f)(*a, **kw)

            return decorator(*args, **kwargs)(ensure_sync)
        return inner_patched_decorator
    return patched_decorator


def patch_decorator_method(class_, method_name):
    original_decorator = getattr(class_, method_name)

    def patched_decorator_method(self, f):
        @wraps(f)
        def ensure_sync(*a, **kw):
            return current_app.ensure_sync(f)(*a, **kw)

        return original_decorator(self, ensure_sync)
    return patched_decorator_method


def patch_decorator_method_with_args(class_, method_name):
    original_decorator = getattr(class_, method_name)

    def patched_decorator_method(self, *args, **kwargs):
        def inner_patched_decorator_method(f):
            @wraps(f)
            def ensure_sync(*a, **kw):
                return current_app.ensure_sync(f)(*a, **kw)

            return original_decorator(self, *args, **kwargs)(ensure_sync)
        return inner_patched_decorator_method
    return patched_decorator_method
