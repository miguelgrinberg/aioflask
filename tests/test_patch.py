import unittest
import aioflask
import aioflask.patch


class TestPatch(unittest.TestCase):
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
