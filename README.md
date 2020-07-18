# aioflask
Flask running on asyncio!

WARNING: This is an experiment at this point. Not at all production ready!

## Quick start

To use async view functions and other handlers, import the `Flask` class from
`aioflask` instead of from `flask`. All other symbols should be imported from
their original packages, be it `flask`, `werkzeug`, etc.

The `aioflask.Flask` class is a subclass of `flask.Flask` that changes a few
minor things to help the application run properly under the asyncio loop. In
particular, it does the following things:

- It wraps any application handlers that are async functions with
`greenletio.await_` so that they can be invoked as normal functions (while
retaining their async properties).
- It modifies the application and request context stacks so that context
locals apply to async tasks instead of to system threads.
- It replaces the WSGI callable with an ASGI callable
- It overrides the `run()` method to use uvicorn as web server.

The `flask run` command is also overriden to start the uvicorn web server.

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
