import aiohttp
from aioflask import Flask

app = Flask(__name__)


@app.route('/')
async def index():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.quotable.io/random') as resp:
            quote = await resp.json()
            return f'''<!doctype html>
<html>
  <head>
    <title>Quotes</title>
  </head>
  <body>
    <h1>Quotes</h1>
    <p><i>"{quote['content']}"</i> &mdash; {quote['author']}</p>
  </body>
</html>'''
