import asyncio
from greenletio.core import bridge


def async_test(f):
    def wrapper(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))
        bridge.stop()
        bridge.reset()

    return wrapper
