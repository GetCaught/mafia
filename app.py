import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import random
from pytz import timezone
import pytz
from flask import jsonify


app = Flask(__name__)
app.config['DATABASE'] = 'users.db'
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
        with app.app_context():
            cursor = get_db().cursor()
            username = request.form['username']
            password = request.form['password']

            cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[1], password):
                return redirect(url_for('login_success', username=username))
            else:
                flash("Incorrect login. Please try again.", "error")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        with app.app_context():
            cursor = get_db().cursor()
            username = request.form['username']
            password = request.form['password']

            cursor.execute("SELECT id FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user:
                flash("Username already exists. Please choose a different username.", "error")
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                get_db().commit()
                flash("Congratulations! You have successfully registered.", "success")
                return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with app.app_context():
            cursor = get_db().cursor()
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
    with app.app_context():
        # Fetch active lobby rooms
        cursor = get_db().cursor()
        cursor.execute("SELECT creator FROM lobbies")
        active_lobbies = cursor.fetchall()

        return render_template('login_success.html', username=username, active_lobbies=active_lobbies)




# ... your other imports ...

@app.route('/lobby_room/<name>', methods=['GET'])
def lobby_room(name):
    print("Received name from URL:", name)
    with app.app_context():
        print("Fetching lobby data for creator:", name)
        cursor = get_db().cursor()
        cursor.execute("SELECT pin, creation_time FROM lobbies WHERE creator=?", (name,))
        lobby_data = cursor.fetchone()
        print("Fetched lobby data:", lobby_data)

        if lobby_data:
            pin = lobby_data[0]
            creation_time = lobby_data[1]
            print("Is NOW CREATED", creation_time)
            if creation_time is None or (datetime.now() - creation_time).total_seconds() > 24 * 60 * 60:
                # Generate a new PIN and update the database
                new_pin = ''.join(random.choices(string.digits, k=6))
                print("Generated new PIN:", new_pin)
                cursor.execute("UPDATE lobbies SET pin=?, creation_time=? WHERE creator=?", (new_pin, datetime.now(), name))
                get_db().commit()
                pin = new_pin
        else:
            # Insert lobby data into 'lobbies' table
            new_pin = ''.join(random.choices(string.digits, k=6))
            print("Generated new PIN:", new_pin)
            cursor.execute("INSERT INTO lobbies (creator, pin, creation_time) VALUES (?, ?, ?)", (name, new_pin, datetime.now()))
            get_db().commit()
            pin = new_pin

        print("PIN Value:", pin)

        # Fetch participants' data (modify this query as needed)
        cursor.execute("SELECT participant FROM participants_table WHERE lobby_name=?", (name,))
        participants = [row[0] for row in cursor.fetchall()]
        print("Participants:", participants)

    return render_template('lobby_room.html', lobby_name=name, pin=pin, participants=participants)





# ... your other imports ...

@app.route('/create_lobby', methods=['POST'])
def create_lobby():
    with app.app_context():
        cursor = get_db().cursor()
        username = request.form['username']  # Make sure to get the username
        cursor.execute("SELECT id FROM lobbies WHERE creator=?", (username,))
        existing_lobby = cursor.fetchone()

        if existing_lobby:
            flash("You already have an existing lobby.", "error")
        else:
            # Set the time zone to Central European Time (CET)
            cet = pytz.timezone('Europe/Copenhagen')

            # Get the current time in CET
            current_time_cet = datetime.now(cet)
            print("Creating lobby for username:", username)
            # Generate a random PIN of six digits
            pin = ''.join(random.choices(string.digits, k=6))
            print("Generated PIN:", pin)
            print("Lobby created successfully with PIN:", pin)
            print("Inserting lobby for username:", username, "with PIN:", pin)
            cursor.execute("INSERT INTO lobbies (creator, pin, creation_time) VALUES (?, ?, ?)", (username, pin, current_time_cet))
            get_db().commit()  # Commit the changes to the database
            print("Lobby inserted successfully.")
            flash("Lobby created successfully.", "success")

    return redirect(url_for('login_success', username=username))

# ... (your other imports) ...

from flask import jsonify

# ... existing code ...

@app.route('/join_lobby', methods=['POST'])
def join_lobby():
    if request.method == 'POST':
        with app.app_context():
            cursor = get_db().cursor()
            username = request.form['username']  # Participant's username
            lobby_name = request.form['lobby_name']  # Lobby name entered by user
            pin = request.form['pin']  # PIN code entered by user

            # Check if the entered lobby name and PIN code match an existing lobby
            cursor.execute("SELECT id FROM lobbies WHERE creator=? AND pin=?", (lobby_name, pin))
            existing_lobby = cursor.fetchone()

            if existing_lobby:
                # Add participant to the participants_table
                cursor.execute("INSERT INTO participants_table (lobby_name, participant) VALUES (?, ?)", (lobby_name, username))
                get_db().commit()
                flash("You have successfully joined the lobby.", "success")

                # Return a JSON response indicating success
                return jsonify({"success": True})
            else:
                flash("Invalid lobby name or PIN code. Please try again.", "error")
                # Return a JSON response indicating failure
                return jsonify({"success": False})

                    
    return redirect(url_for('login_success', username=username))  # Redirect to the home page or a suitable page

@app.route('/get_available_lobbies', methods=['GET'])
def get_available_lobbies():
    with app.app_context():
        cursor = get_db().cursor()

        # Query the 'lobbies' table to get the list of available lobbies
        cursor.execute("SELECT DISTINCT creator FROM lobbies")
        available_lobbies = [row[0] for row in cursor.fetchall()]

        return jsonify({"success": True, "lobbies": available_lobbies})



app.config['DEBUG'] = True

# ... other imports ...

if __name__ == '__main__':
    with app.app_context():
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lobbies (
                id INTEGER PRIMARY KEY,
                creator TEXT NOT NULL,
                pin TEXT NOT NULL,
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants_table (
                id INTEGER PRIMARY KEY,
                lobby_name TEXT NOT NULL,
                participant TEXT NOT NULL
            )
        ''')
        lobbies_db_path = 'users.db'
        twelwe_hours_ago = datetime.now() - timedelta(hours=12)
        lobbies_connection = sqlite3.connect(lobbies_db_path)
        lobbies_cursor = lobbies_connection.cursor()
        cursor.execute("DELETE FROM lobbies WHERE creation_time < ?", (twelwe_hours_ago,))
        lobbies_connection.commit()
        lobbies_connection.close()
        conn.commit()
        conn.close()

    app.run()