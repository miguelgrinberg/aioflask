import os
import unittest
from unittest import mock
import click
from click.testing import CliRunner
import aioflask
import aioflask.cli


class TestCli(unittest.TestCase):
    def test_command_with_appcontext(runner):
        app = aioflask.Flask('testapp')

        @app.cli.command(with_appcontext=True)
        async def testcmd():
            click.echo(aioflask.current_app.name)

        obj = aioflask.cli.ScriptInfo(create_app=lambda: app)

        result = CliRunner().invoke(testcmd, obj=obj)
        assert result.exit_code == 0
        assert result.output == "testapp\n"

    def test_command_without_appcontext(runner):
        app = aioflask.Flask('testapp')

        @app.cli.command(with_appcontext=False)
        async def testcmd():
            click.echo(aioflask.current_app.name)

        obj = aioflask.cli.ScriptInfo(create_app=lambda: app)

        result = CliRunner().invoke(testcmd, obj=obj)
        assert result.exit_code == 1
        assert type(result.exception) == RuntimeError

    def test_with_appcontext(runner):
        @click.command()
        @aioflask.cli.with_appcontext
        async def testcmd():
            click.echo(aioflask.current_app.name)

        obj = aioflask.cli.ScriptInfo(
            create_app=lambda: aioflask.Flask('testapp'))

        result = CliRunner().invoke(testcmd, obj=obj)
        assert result.exit_code == 0
        assert result.output == "testapp\n"

    @mock.patch('aioflask.cli.uvicorn')
    def test_aiorun(self, uvicorn):
        app = aioflask.Flask('testapp')
        obj = aioflask.cli.ScriptInfo(app_import_path='app.py',
                                      create_app=lambda: app)

        result = CliRunner().invoke(aioflask.cli.run_command, obj=obj)
        assert result.exit_code == 0
        uvicorn.run.assert_called_with('app:app', factory=False,
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        result = CliRunner().invoke(aioflask.cli.run_command,
                                    '--host 1.2.3.4 --port 3000', obj=obj)
        assert result.exit_code == 0
        uvicorn.run.assert_called_with('app:app', factory=False,
                                       host='1.2.3.4', port=3000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
        os.environ['FLASK_DEBUG'] = 'true'
        result = CliRunner().invoke(aioflask.cli.run_command, obj=obj)
        assert result.exit_code == 0
        uvicorn.run.assert_called_with('app:app', factory=False,
                                       host='127.0.0.1', port=5000,
                                       reload=True, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)
        os.environ['FLASK_DEBUG'] = 'true'
        result = CliRunner().invoke(aioflask.cli.run_command, '--no-reload',
                                    obj=obj)
        assert result.exit_code == 0
        uvicorn.run.assert_called_with('app:app', factory=False,
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='debug', ssl_certfile=None,
                                       ssl_keyfile=None)

        if 'FLASK_DEBUG' in os.environ:
            del os.environ['FLASK_DEBUG']
        if 'AIOFLASK_USE_DEBUGGER' in os.environ:
            del os.environ['AIOFLASK_USE_DEBUGGER']

    @mock.patch('aioflask.cli.uvicorn')
    def test_aiorun_with_factory(self, uvicorn):
        app = aioflask.Flask('testapp')
        obj = aioflask.cli.ScriptInfo(app_import_path='app:create_app()',
                                      create_app=lambda: app)

        result = CliRunner().invoke(aioflask.cli.run_command, obj=obj)
        assert result.exit_code == 0
        uvicorn.run.assert_called_with('app:create_app', factory=True,
                                       host='127.0.0.1', port=5000,
                                       reload=False, workers=1,
                                       log_level='info', ssl_certfile=None,
                                       ssl_keyfile=None)
