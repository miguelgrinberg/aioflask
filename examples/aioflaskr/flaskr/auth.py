from aioflask import Blueprint
from aioflask import flash
from aioflask import redirect
from aioflask import render_template
from aioflask import request
from aioflask import url_for
from aioflask.patched.flask_login import login_user
from aioflask.patched.flask_login import logout_user
from sqlalchemy.exc import IntegrityError

from flaskr import db, login
from flaskr.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@login.user_loader
async def load_user(id):
    return await db.session.get(User, int(id))


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

        if error is None:
            try:
                db.session.add(User(username=username, password=password))
                await db.session.commit()
            except IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = f"User {username} is already registered."
            else:
                # Success, go to the login page.
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

        query = User.select().filter_by(username=username)
        user = await db.session.scalar(query)

        if user is None:
            error = "Incorrect username."
        elif not user.check_password(password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            login_user(user)
            return redirect(url_for("index"))

        flash(error)

    return await render_template("auth/login.html")


@bp.route("/logout")
async def logout():
    """Clear the current session, including the stored user id."""
    logout_user()
    return redirect(url_for("index"))
