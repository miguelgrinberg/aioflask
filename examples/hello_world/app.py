from aioflask import Flask, render_template

app = Flask(__name__)


@app.route('/')
async def index():
    return await render_template('index.html')


@app.cli.command()
async def hello():
    """Example async CLI handler."""
    print('hello!')
