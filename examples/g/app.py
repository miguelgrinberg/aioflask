from aioflask import Flask, g
import aiohttp

app = Flask(__name__)


@app.before_request
async def before_request():
    g.session = aiohttp.ClientSession()


@app.teardown_appcontext
async def teardown_appcontext(exc):
    await g.session.close()


@app.route('/')
async def index():
    response = await g.session.get('https://api.quotable.io/random')
    return (await response.json())['content']
