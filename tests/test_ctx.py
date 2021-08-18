import unittest
import pytest
import aioflask
from .utils import async_test


class TestApp(unittest.TestCase):
    @async_test
    async def test_app_context(self):
        app = aioflask.Flask(__name__)
        called_t1 = False
        called_t2 = False

        @app.teardown_appcontext
        async def t1(exc):
            nonlocal called_t1
            called_t1 = True

        @app.teardown_appcontext
        def t2(exc):
            nonlocal called_t2
            called_t2 = True

        async with app.app_context():
            assert aioflask.current_app == app
            async with app.app_context():
                assert aioflask.current_app == app
            assert aioflask.current_app == app

        assert called_t1
        assert called_t2
        with pytest.raises(RuntimeError):
            print(aioflask.current_app)

    @async_test
    async def test_req_context(self):
        app = aioflask.Flask(__name__)
        called_t1 = False
        called_t2 = False

        @app.teardown_appcontext
        async def t1(exc):
            nonlocal called_t1
            called_t1 = True

        @app.teardown_appcontext
        def t2(exc):
            nonlocal called_t2
            called_t2 = True

        async with app.test_request_context('/foo'):
            assert aioflask.current_app == app
            assert aioflask.request.path == '/foo'

        assert called_t1
        assert called_t2

        async with app.app_context():
            async with app.test_request_context('/bar') as reqctx:
                assert aioflask.current_app == app
                assert aioflask.request.path == '/bar'
                async with reqctx:
                    assert aioflask.current_app == app
                    assert aioflask.request.path == '/bar'

        with pytest.raises(RuntimeError):
            print(aioflask.current_app)
