import sqlite3
from flask import Flask, render_template, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

conn = sqlite3.connect('example.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )''')

conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            return "Login successful!"

        return "Invalid username or password!"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            return redirect(url_for('registration_status', status='failure'))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()

        return redirect(url_for('registration_status', status='success'))

    return render_template('register.html')

@app.route('/registration_status')
def registration_status():
    status = request.args.get('status')
    if status == 'success':
        return render_template('registration_success.html', message='Congratulations! You have successfully registered.')
    elif status == 'failure':
        return render_template('registration_failure.html', message='Registration failed. Please choose a different username.')
    else:
        return "Invalid registration status."


if __name__ == '__main__':
    app.run()
