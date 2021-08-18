import asyncio
from greenletio.core import bridge


def async_test(f):
    def wrapper(*args, **kwargs):
        asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))

    return wrapper
