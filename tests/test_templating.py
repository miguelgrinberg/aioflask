import asyncio
import os
import unittest
from unittest import mock
import aioflask
from .utils import async_test


class TestTemplating(unittest.TestCase):
    @async_test
    async def test_template_strng(self):
        app = aioflask.Flask(__name__)
        app.secret_key = 'secret'

        @app.before_request
        def before_request():
            aioflask.g.x = 'foo'
            aioflask.session['y'] = 'bar'

        @app.route('/')
        async def async_route():
            return await aioflask.render_template_string(
                '{{ g.x }}{{ session.y }}')

        client = app.test_client()
        response = await client.get('/')
        assert response.data == b'foobar'

    @async_test
    async def test_template(self):
        app = aioflask.Flask(__name__)
        app.secret_key = 'secret'

        @app.before_request
        def before_request():
            aioflask.g.x = 'foo'
            aioflask.session['y'] = 'bar'

        @app.route('/')
        async def async_route():
            return await aioflask.render_template('template.html')

        client = app.test_client()
        response = await client.get('/')
        assert response.data == b'foobar'
