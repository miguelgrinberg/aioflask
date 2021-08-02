import functools

from aioflask import Blueprint
from aioflask import current_app
from aioflask import flash
from aioflask import g
from aioflask import redirect
from aioflask import render_template
from aioflask import request
from aioflask import session
from aioflask import url_for

from flaskr import db
from flaskr.auth.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return current_app.ensure_sync(view)(**kwargs)

    return wrapped_view


@bp.before_app_request
async def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")
    async with db.session() as dbsession:
        g.user = await dbsession.get(User, user_id) \
            if user_id is not None else None


@bp.route("/register", methods=("GET", "POST"))
async def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        else:
            async with db.session() as dbsession:
                if (await dbsession.execute(db.select(User).filter_by(
                        username=username))).scalars().first():
                    print('**** already')
                    error = f"User {username} is already registered."

                if error is None:
                    # the name is available, create the user and go to the
                    # login page
                    async with dbsession.begin_nested():
                        dbsession.add(User(
                            username=username, password=password))
                    return redirect(url_for("auth.login"))

        flash(error)

    return await render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
async def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        async with db.session() as dbsession:
            user = (await dbsession.execute(db.select(User).filter_by(
                username=username))).scalars().first()

        if user is None:
            error = "Incorrect username."
        elif not user.check_password(password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return await render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
