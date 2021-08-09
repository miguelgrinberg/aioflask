from functools import wraps
from inspect import iscoroutinefunction
import os
import sys

from flask.cli import *
from flask.cli import AppGroup, ScriptInfo, update_wrapper, \
    SeparatedPathType, pass_script_info, get_debug_flag, NoAppException, \
    prepare_import
from flask.cli import _validate_key
from flask.globals import _app_ctx_stack
from flask.helpers import get_env
from greenletio import await_
from werkzeug.utils import import_string
import click
import uvicorn

try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None

OriginalAppGroup = AppGroup


def _ensure_sync(func, with_appcontext=False):
    if not iscoroutinefunction(func):
        return func

    def decorated(*args, **kwargs):
        if with_appcontext:
            appctx = _app_ctx_stack.top

            @await_
            async def _coro():
                with appctx:
                    return await func(*args, **kwargs)
        else:
            @await_
            async def _coro():
                return await func(*args, **kwargs)

        return _coro()

    return decorated


def with_appcontext(f):
    """Wraps a callback so that it's guaranteed to be executed with the
    script's application context.  If callbacks are registered directly
    to the ``app.cli`` object then they are wrapped with this function
    by default unless it's disabled.
    """

    @click.pass_context
    def decorator(__ctx, *args, **kwargs):
        with __ctx.ensure_object(ScriptInfo).load_app().app_context():
            return __ctx.invoke(_ensure_sync(f, True), *args, **kwargs)

    return update_wrapper(decorator, f)


class AppGroup(OriginalAppGroup):
    """This works similar to a regular click :class:`~click.Group` but it
    changes the behavior of the :meth:`command` decorator so that it
    automatically wraps the functions in :func:`with_appcontext`.
    Not to be confused with :class:`FlaskGroup`.
    """

    def command(self, *args, **kwargs):
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it wraps callbacks in :func:`with_appcontext`
        unless it's disabled by passing ``with_appcontext=False``.
        """
        wrap_for_ctx = kwargs.pop("with_appcontext", True)

        def decorator(f):
            if wrap_for_ctx:
                f = with_appcontext(f)
            return click.Group.command(self, *args, **kwargs)(_ensure_sync(f))

        return decorator


def show_server_banner(env, debug, app_import_path, eager_loading):
    """Show extra startup messages the first time the server is run,
    ignoring the reloader.
    """
    if app_import_path is not None:
        message = f" * Serving Flask app {app_import_path!r}"

        click.echo(message)

    click.echo(f" * Environment: {env}")

    if debug is not None:
        click.echo(f" * Debug mode: {'on' if debug else 'off'}")


class CertParamType(click.ParamType):
    """Click option type for the ``--cert`` option. Allows either an
    existing file, the string ``'adhoc'``, or an import for a
    :class:`~ssl.SSLContext` object.
    """

    name = "path"

    def __init__(self):
        self.path_type = click.Path(exists=True, dir_okay=False,
                                    resolve_path=True)

    def convert(self, value, param, ctx):
        if ssl is None:
            raise click.BadParameter('Using "--cert" requires Python to be '
                                     'compiled with SSL support.',
                                     ctx, param)

        try:
            return self.path_type(value, param, ctx)
        except click.BadParameter:
            value = click.STRING(value, param, ctx).lower()

            if value == "adhoc":
                raise click.BadParameter("Aad-hoc certificates are currently "
                                         "not supported by aioflask.",
                                         ctx, param)

                return value

            obj = import_string(value, silent=True)

            if isinstance(obj, ssl.SSLContext):
                return obj

            raise


@click.command("run", short_help="Run a development server.")
@click.option("--host", "-h", default="127.0.0.1",
              help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option(
    "--cert", type=CertParamType(),
    help="Specify a certificate file to use HTTPS."
)
@click.option(
    "--key",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    callback=_validate_key,
    expose_value=False,
    help="The key file to use when specifying a certificate.",
)
@click.option(
    "--reload/--no-reload",
    default=None,
    help="Enable or disable the reloader. By default the reloader "
    "is active if debug is enabled.",
)
@click.option(
    "--debugger/--no-debugger",
    default=None,
    help="Enable or disable the debugger. By default the debugger "
    "is active if debug is enabled.",
)
@click.option(
    "--eager-loading/--lazy-loading",
    default=None,
    help="Enable or disable eager loading. By default eager "
    "loading is enabled if the reloader is disabled.",
)
@click.option(
    "--with-threads/--without-threads",
    default=True,
    help="Enable or disable multithreading.",
)
@click.option(
    "--extra-files",
    default=None,
    type=SeparatedPathType(),
    help=(
        "Extra files that trigger a reload on change. Multiple paths"
        f" are separated by {os.path.pathsep!r}."
    ),
)
@pass_script_info
def run_command(info, host, port, reload, debugger, eager_loading,
                with_threads, cert, extra_files):
    """Run a local development server.
    This server is for development purposes only. It does not provide
    the stability, security, or performance of production WSGI servers.
    The reloader and debugger are enabled by default if
    FLASK_ENV=development or FLASK_DEBUG=1.
    """
    debug = get_debug_flag()

    if reload is None:
        reload = debug

    if debugger is None:
        debugger = debug
    if debugger:
        os.environ['AIOFLASK_USE_DEBUGGER'] = 'true'

    certfile = None
    keyfile = None
    if cert is not None and len(cert) == 2:
        certfile = cert[0]
        keyfile = cert[1]

    show_server_banner(get_env(), debug, info.app_import_path, eager_loading)

    app_import_path = info.app_import_path
    if app_import_path is None:
        for path in ('wsgi', 'app'):
            if os.path.exists(path) or os.path.exists(path + '.py'):
                app_import_path = path
                break
        if app_import_path is None:
            raise NoAppException(
                "Could not locate a Flask application. You did not provide "
                'the "FLASK_APP" environment variable, and a "wsgi.py" or '
                '"app.py" module was not found in the current directory.'
            )
    if app_import_path.endswith('.py'):
        app_import_path = app_import_path[:-3]

    factory = False
    if app_import_path.endswith('()'):
        # TODO: this needs to be expanded to accept arguments for the factory
        # function
        app_import_path = app_import_path[:-2]
        factory = True

    if ':' not in app_import_path:
        app_import_path += ':app'

    import_name, app_name = app_import_path.split(':')
    import_name = prepare_import(import_name)

    uvicorn.run(
        import_name + ':' + app_name,
        factory=factory,
        host=host,
        port=port,
        reload=reload,
        workers=1,
        log_level='debug' if debug else 'info',
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
    )

    # currently not supported:
    # - eager_loading
    # - with_threads
    # - adhoc certs
    # - extra_files
