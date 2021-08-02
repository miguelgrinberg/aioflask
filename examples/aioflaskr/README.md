# AioFlaskr

The basic blog app built in the Flask [tutorial](https://flask.palletsprojects.com/tutorial/),
modified to use asyncio and [aioflask](https://github.com/miguelgrinberg/aioflask),
with a [SQLAlchemy](https://docs.sqlalchemy.org/) database managed by the
[Alchemical](https://github.com/miguelgrinberg/alchemical) extension.

## Install

    # clone the repository
    $ git clone https://github.com/miguelgrinberg/aioflask
    $ cd aioflask/examples/aioflaskr

Create a virtualenv and activate it:

    $ python3 -m venv venv
    $ . venv/bin/activate

Or on Windows cmd:

    $ py -3 -m venv venv
    $ venv\Scripts\activate.bat

Install the dependencies:

    $ pip install -r requirements.txt

## Run

    $ flask init-db
    $ flask aiorun

Or on Windows cmd:

    > flask init-db
    > flask aiorun

Open http://127.0.0.1:5000 in a browser.

## Test

    $ pip install pytest coverage
    $ pytest

Run with coverage report:

    $ coverage run -m pytest
    $ coverage report
    $ coverage html  # open htmlcov/index.html in a browser
