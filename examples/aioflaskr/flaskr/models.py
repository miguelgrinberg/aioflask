from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from aioflask import url_for
from aioflask.patched.flask_login import UserMixin

from flaskr import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    @property
    def password(self):
        raise RuntimeError('Cannot get user passwords!')

    @password.setter
    def password(self, value):
        """Store the password as a hash for security."""
        self.password_hash = generate_password_hash(value)

    def check_password(self, value):
        return check_password_hash(self.password_hash, value)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    created = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)

    # User object backed by author_id
    # lazy="joined" means the user is returned with the post in one query
    author = db.relationship(User, lazy="joined", backref="posts")

    @property
    def update_url(self):
        return url_for("blog.update", id=self.id)

    @property
    def delete_url(self):
        return url_for("blog.delete", id=self.id)
