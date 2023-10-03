import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['DATABASE'] = 'users.db'

# Generate a secure secret key with 32 bytes
app.secret_key = secrets.token_hex(32)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        with app.app_context():  # Create an application context here
            cursor = get_db().cursor()  # Access the database within the context
            username = request.form['username']
            password = request.form['password']

            cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[1], password):
                return redirect(url_for('login_success', username=username))
            else:
                flash("Incorrect login. Please try again.", "error")

    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with app.app_context():  # Create an application context here
            cursor = get_db().cursor()  # Access the database within the context
            username = request.form['username']
            password = request.form['password']

            cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[1], password):
                return redirect(url_for('login_success', username=username))
            else:
                flash("Incorrect login. Please try again.", "error")

    return render_template('login.html')

@app.route('/login_success')
def login_success():
    username = request.args.get('username')
    return render_template('login_success.html', username=username)

# Other routes and code...

if __name__ == '__main__':
    app.run()
