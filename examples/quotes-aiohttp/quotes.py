import asyncio
import aiohttp
from aioflask import Flask, render_template_string

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


async def get_quote(session):
    response = await session.get('https://api.quotable.io/random')
    return await response.json()


@app.route('/')
async def index():
    async with aiohttp.ClientSession() as session:
        tasks = [get_quote(session) for _ in range(10)]
        quotes = await asyncio.gather(*tasks)
    return await render_template_string(template, quotes=quotes)
