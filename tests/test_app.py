import asyncio
import os
import unittest
from unittest import mock
import aioflask
from .utils import async_test


class TestApp(unittest.TestCase):
    @async_test
    async def test_app(self):
        app = aioflask.Flask(__name__)

        @app.route('/async')
        async def async_route():
            await asyncio.sleep(0)
            assert aioflask.current_app._get_current_object() == app
            return 'async'

        @app.route('/sync')
        def sync_route():
            assert aioflask.current_app._get_current_object() == app
            return 'sync'

        client = app.test_client()
        response = await client.get('/async')
        assert response.data == b'async'
        response = await client.get('/sync')
        assert response.data == b'sync'

    @async_test
    async def test_g(self):
        app = aioflask.Flask(__name__)
        app.secret_key = 'secret'

        @app.before_request
        async def async_before_request():
            aioflask.g.asyncvar = 'async'

        @app.before_request
        def sync_before_request():
            aioflask.g.syncvar = 'sync'

        @app.route('/async')
        async def async_route():
            aioflask.session['a'] = 'async'
            return f'{aioflask.g.asyncvar}-{aioflask.g.syncvar}'

        @app.route('/sync')
        async def sync_route():
            aioflask.session['s'] = 'sync'
            return f'{aioflask.g.asyncvar}-{aioflask.g.syncvar}'

        @app.route('/session')
        async def session():
            return f'{aioflask.session.get("a")}-{aioflask.session.get("s")}'

        @app.after_request
        async def after_request(rv):
            rv.data += f'/{aioflask.g.asyncvar}-{aioflask.g.syncvar}'.encode()
            return rv

        client = app.test_client()
        response = await client.get('/session')
        assert response.data == b'None-None/async-sync'
        response = await client.get('/async')
        assert response.data == b'async-sync/async-sync'
        response = await client.get('/session')
        assert response.data == b'async-None/async-sync'
        response = await client.get('/sync')
        assert response.data == b'async-sync/async-sync'
        response = await client.get('/session')
        assert response.data == b'async-sync/async-sync'

    @mock.patch('aioflask.app.uvicorn')
    def test_app_run(self, uvicorn):
        app = aioflask.Flask(__name__)

        app.run()
        uvicorn.run.assert_called_with('tests.test_app:app',
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(host='1.2.3.4', port=3000)
        uvicorn.run.assert_called_with('tests.test_app:app',
                                       host='1.2.3.4', port=3000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(debug=True)
        uvicorn.run.assert_called_with('tests.test_app:app',
                                       host='127.0.0.1', port=5000,
                                       reload=True, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(debug=True, use_reloader=False)
        uvicorn.run.assert_called_with('tests.test_app:app',
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
        if 'FLASK_DEBUG' in os.environ:
            del os.environ['FLASK_DEBUG']
        if 'AIOFLASK_USE_DEBUGGER' in os.environ:
            del os.environ['AIOFLASK_USE_DEBUGGER']
