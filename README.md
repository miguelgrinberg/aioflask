# aioflask

![Build status](https://github.com/miguelgrinberg/aioflask/workflows/build/badge.svg) [![codecov](https://codecov.io/gh/miguelgrinberg/aioflask/branch/master/graph/badge.svg?token=CDMKF3L0ID)](https://codecov.io/gh/miguelgrinberg/aioflask)

Flask running on asyncio!

WARNING: This is an experiment at this point. Not at all production ready!

## Quick start

To use async view functions and other handlers, use the `aioflask` package
instead of `flask`.

The `aioflask.Flask` class is a subclass of `flask.Flask` that changes a few
minor things to help the application run properly under the asyncio loop. In
particular, it overrides the following aspects of the application instance:

- The `route`, `before_request`, `before_first_request`, `after_request`, 
  `teardown_request`, `teardown_appcontext`, `errorhandler` and `cli.command`
  decorators accept coroutines as well as regular functions. The handlers all
  run inside an asyncio loop, so when using regular functions, care must be
  taken to not block.
- The WSGI callable entry point is replaced with an ASGI equivalent.
- The `run()` method uses uvicorn as web server.

There are also changes outside of the `Flask` class:

- The `flask run` command starts the uvicorn web server.
- The `render_template()` function is asynchronous and must be awaited. The
  sync render version is available as `render_template_sync()`.

## Example

```python
import asyncio
from aioflask import Flask

app = Flask(__name__)

@app.route('/')
async def index():
    await asyncio.sleep(1)
    return "Look Ma, I'm async!"
```
