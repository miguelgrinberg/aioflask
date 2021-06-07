import asyncio
import unittest
from unittest import mock
from aioflask import Flask, current_app


class TestAioflask(unittest.TestCase):
    def test_app(self):
        app = Flask(__name__)

        @app.route('/async')
        async def async_route():
            await asyncio.sleep(0)
            assert current_app._get_current_object() == app
            return 'async'

        @app.route('/sync')
        def sync_route():
            assert current_app._get_current_object() == app
            return 'sync'

        app._fix_async()

        client = app.test_client()
        response = client.get('/async')
        assert response.data == b'async'
        response = client.get('/sync')
        assert response.data == b'sync'

    @mock.patch('aioflask.app.uvicorn')
    def test_app_run(self, uvicorn):
        app = Flask(__name__)

        app.run()
        uvicorn.run.assert_called_with('tests.test_aioflask:app',
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(host='1.2.3.4', port=3000)
        uvicorn.run.assert_called_with('tests.test_aioflask:app',
                                       host='1.2.3.4', port=3000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(debug=True)
        uvicorn.run.assert_called_with('tests.test_aioflask:app',
                                       host='127.0.0.1', port=5000,
                                       reload=True, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(debug=True)
        uvicorn.run.assert_called_with('tests.test_aioflask:app',
                                       host='127.0.0.1', port=5000,
                                       reload=True, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
        app.run(debug=True, use_reloader=False)
        uvicorn.run.assert_called_with('tests.test_aioflask:app',
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
