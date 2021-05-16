import asyncio
from aioflask import Flask, render_template_string
from greenletio import async_
import requests

app = Flask(__name__)
template = '''<!doctype html>
<html>
  <head>
    <title>Quotes</title>
  </head>
  <body>
    <h1>Quotes</h1>
    {% for quote in quotes %}
    <p><i>"{{ quote.content }}"</i> &mdash; {{ quote.author }}</p>
    {% endfor %}
  </body>
</html>'''


# this is a blocking function that is converted to asynchronous with
# greenletio's @async_ decorator. For this to work, all the low-level I/O
# functions started from this function must be asynchronous, which can be
# achieved with greenletio's monkey patching feature.
@async_
def get_quote():
    response = requests.get('https://api.quotable.io/random')
    return response.json()


@app.route('/')
async def index():
    tasks = [get_quote() for _ in range(10)]
    quotes = await asyncio.gather(*tasks)
    return await render_template_string(template, quotes=quotes)
