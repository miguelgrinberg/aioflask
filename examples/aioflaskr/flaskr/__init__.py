import os

import click
from aioflask import Flask
from aioflask.cli import with_appcontext
from alchemical.aioflask import Alchemical
from aioflask.patched.flask_login import LoginManager

db = Alchemical()
login = LoginManager()
login.login_view = 'auth.login'


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # some deploy systems set the database url in the environ
    db_url = os.environ.get("DATABASE_URL")

    if db_url is None:
        # default to a sqlite database in the instance folder
        db_path = os.path.join(app.instance_path, "flaskr.sqlite")
        db_url = f"sqlite:///{db_path}"
        # ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        ALCHEMICAL_DATABASE_URL=db_url,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # initialize Flask-Alchemical and the init-db command
    db.init_app(app)
    app.cli.add_command(init_db_command)

    # initialize Flask-Login
    login.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth, blog

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)

    # make "index" point at "/", which is handled by "blog.index"
    app.add_url_rule("/", endpoint="index")

    return app


async def init_db():
    await db.drop_all()
    await db.create_all()


@click.command("init-db")
@with_appcontext
async def init_db_command():
    """Clear existing data and create new tables."""
    await init_db()
    click.echo("Initialized the database.")
