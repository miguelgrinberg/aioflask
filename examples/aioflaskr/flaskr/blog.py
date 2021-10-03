from aioflask import Blueprint
from aioflask import flash
from aioflask import redirect
from aioflask import render_template
from aioflask import request
from aioflask import url_for
from werkzeug.exceptions import abort
from aioflask.patched.flask_login import current_user
from aioflask.patched.flask_login import login_required

from flaskr import db
from flaskr.models import Post

bp = Blueprint("blog", __name__)


@bp.route("/")
async def index():
    """Show all the posts, most recent first."""
    posts = (await db.session.scalars(Post.select())).all()
    return await render_template("blog/index.html", posts=posts)


async def get_post(id, check_author=True):
    """Get a post and its author by id.
    Checks that the id exists and optionally that the current user is
    the author.
    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = await db.session.get(Post, id)

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post.author != current_user:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
async def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db.session.add(Post(title=title, body=body, author=current_user))
            await db.session.commit()
            return redirect(url_for("blog.index"))

    return await render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
async def update(id):
    """Update a post if the current user is the author."""
    post = await get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            await db.session.commit()
            return redirect(url_for("blog.index"))

    return await render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
async def delete(id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    post = await get_post(id)
    await db.session.delete(post)
    await db.session.commit()
    return redirect(url_for("blog.index"))
