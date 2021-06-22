from aioflask import Flask, request, redirect
from aioflask.patched.flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import aiohttp

app = Flask(__name__)
app.secret_key = 'top-secret!'
login = LoginManager(app)
login.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/')
@login_required
async def index():
    return f'''
<html>
  <body>
    <p>Logged in user: {current_user.id}</p>
    <form method="POST" action="/logout">
      <input type="submit" value="Logout">
    </form>
  </body>
</html>'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
<html>
  <body>
    <form method="POST" action="">
      <input type="text" name="username">
      <input type="submit" value="Login">
    </form>
  </body>
</html>'''
    else:
        login_user(User(request.form['username']))
        return redirect(request.args.get('next', '/'))


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect('/')
