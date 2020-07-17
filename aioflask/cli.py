import asyncio
import os

from flask.cli import pass_script_info, get_debug_flag, run_command, \
    _validate_key, SeparatedPathType
from flask.helpers import get_env
from werkzeug.utils import import_string
import click
import uvicorn

try:
    import ssl
except ImportError:
    ssl = None


def show_server_banner(env, debug, app_import_path, eager_loading):
    """Show extra startup messages the first time the server is run,
    ignoring the reloader.
    """
    #if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    #    return

    if app_import_path is not None:
        message = f" * Serving Flask app {app_import_path!r}"

        #if not eager_loading:
        #    message += " (lazy loading)"

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
        self.path_type = click.Path(exists=True, dir_okay=False, resolve_path=True)

    def convert(self, value, param, ctx):
        if ssl is None:
            raise click.BadParameter(
                'Using "--cert" requires Python to be compiled with SSL support.',
                ctx,
                param,
            )

        try:
            return self.path_type(value, param, ctx)
        except click.BadParameter:
            value = click.STRING(value, param, ctx).lower()

            if value == "adhoc":
                raise click.BadParameter(
                    "Aad-hoc certificates are currently not supported by aioflask.",
                    ctx,
                    param,
                )

                return value

            obj = import_string(value, silent=True)

            if isinstance(obj, ssl.SSLContext):
                return obj

            raise


@click.command("run", short_help="Run a development server.")
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option(
    "--cert", type=CertParamType(), help="Specify a certificate file to use HTTPS."
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
def run(
    info, host, port, reload, debugger, eager_loading, with_threads, cert, extra_files
):
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
    #app = DispatchingApp(info.load_app, use_eager_loading=eager_loading)

    #from werkzeug.serving import run_simple
    app_import_path = info.app_import_path
    if app_import_path.endswith('.py'):
        app_import_path = app_import_path[:-3] + ':app'

    uvicorn.run(
        app_import_path,
        host=host,
        port=port,
        reload=reload,
        workers=1,
        log_level='debug' if debug else 'info',
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
    )
    #run_simple(
    #    host,
    #    port,
    #    app,
    #    use_reloader=reload,
    #    use_debugger=debugger,
    #    threaded=with_threads,
    #    ssl_context=cert,
    #    extra_files=extra_files,
    #)
