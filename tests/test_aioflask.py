import asyncio
import unittest
from unittest import mock
import aioflask
import aioflask.patch


class TestAioflask(unittest.TestCase):
    def test_app(self):
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

        app._fix_async()

        client = app.test_client()
        response = client.get('/async')
        assert response.data == b'async'
        response = client.get('/sync')
        assert response.data == b'sync'

    def test_g(self):
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

        app._fix_async()

        client = app.test_client()
        response = client.get('/session')
        assert response.data == b'None-None/async-sync'
        response = client.get('/async')
        assert response.data == b'async-sync/async-sync'
        response = client.get('/session')
        assert response.data == b'async-None/async-sync'
        response = client.get('/sync')
        assert response.data == b'async-sync/async-sync'
        response = client.get('/session')
        assert response.data == b'async-sync/async-sync'

    def test_decorator(self):
        def foo(f):
            def decorator(*args, **kwargs):
                return f(*args, **kwargs) + '-decorated'

            return decorator

        foo = aioflask.patch.patch_decorator(foo)

        app = aioflask.Flask(__name__)

        @app.route('/abc/<int:id>')
        @foo
        async def abc(id):
            return str(id)

        app._fix_async()

        client = app.test_client()
        response = client.get('/abc/123')
        assert response.data == b'123-decorated'

    def test_decorator_with_args(self):
        def foo(value):
            def inner_foo(f):
                def decorator(*args, **kwargs):
                    return f(*args, **kwargs) + str(value)

                return decorator
            return inner_foo

        foo = aioflask.patch.patch_decorator_with_args(foo)

        app = aioflask.Flask(__name__)

        @app.route('/abc/<int:id>')
        @foo(456)
        async def abc(id):
            return str(id)

        app._fix_async()

        client = app.test_client()
        response = client.get('/abc/123')
        assert response.data == b'123456'

    def test_decorator_method(self):
        class Foo:
            def __init__(self, value):
                self.value = value

            def deco(self, f):
                def decorator(*args, **kwargs):
                    return f(*args, **kwargs) + str(self.value)

                return decorator

        Foo.deco = aioflask.patch.patch_decorator_method(Foo, 'deco')

        app = aioflask.Flask(__name__)
        foo = Foo(456)

        @app.route('/abc/<int:id>')
        @foo.deco
        async def abc(id):
            return str(id)

        app._fix_async()

        client = app.test_client()
        response = client.get('/abc/123')
        assert response.data == b'123456'

    def test_decorator_method_with_args(self):
        class Foo:
            def __init__(self, value):
                self.value = value

            def deco(self, value2):
                def decorator(f):
                    def inner_decorator(*args, **kwargs):
                        return f(*args, **kwargs) + str(self.value) + \
                            str(value2)

                    return inner_decorator
                return decorator

        Foo.deco = aioflask.patch.patch_decorator_method_with_args(Foo, 'deco')

        app = aioflask.Flask(__name__)
        foo = Foo(456)

        @app.route('/abc/<int:id>')
        @foo.deco(789)
        async def abc(id):
            return str(id)

        app._fix_async()

        client = app.test_client()
        response = client.get('/abc/123')
        assert response.data == b'123456789'

    @mock.patch('aioflask.app.uvicorn')
    def test_app_run(self, uvicorn):
        app = aioflask.Flask(__name__)

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
