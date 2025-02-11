from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'fgfgfgf uidihhchh'  


# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="Lab_01_database",  
        user="postgres",  
        password="123" 
    )
    return conn

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if password and confirm password match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        # Check if the user already exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM "Users" WHERE username = %s', (username,))
        user = cur.fetchone()

        if user:
            flash('User already registered!', 'warning')
            return render_template('register.html')

        # If user doesn't exist, insert the new user into the database
        cur.execute('INSERT INTO "Users" (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()

        # Redirect to the login page after successful registration
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM "Users" WHERE username = %s AND password = %s', (username, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]  # Store user id in session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')

# Home route (for logged-in users)
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('home.html')


# Logout route
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect(url_for('login'))  # Redirect to the login page after logout

if __name__ == "__main__":
    app.run(debug=True)
