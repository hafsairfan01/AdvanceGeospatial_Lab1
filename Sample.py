from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'fgfgfgf uidihhchh'

# ------------------------------------------------------------------------------
# 1. Database Connection & Setup
# ------------------------------------------------------------------------------
def get_db_connection():
    """Establishes a connection to PostgreSQL."""
    conn = psycopg2.connect(
        host="localhost",
        database="Lab_01_database",  
        user="postgres",  
        password="123" 
    )
    return conn

def create_reviews_table_if_not_exists():
    """Ensures the Reviews table exists with correct columns/constraints."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Users" (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "books" (
            isbn VARCHAR(20) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            year INTEGER
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Reviews" (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "Users"(id),
            book_isbn VARCHAR(20) NOT NULL REFERENCES "books"(isbn),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, book_isbn)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ------------------------------------------------------------------------------
# 2. User Registration & Login
# ------------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM "Users" WHERE username = %s', (username,))
        user = cur.fetchone()

        if user:
            flash('User already registered!', 'warning')
            cur.close()
            conn.close()
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        cur.execute('INSERT INTO "Users" (username, password) VALUES (%s, %s)', 
                    (username, hashed_password))
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM "Users" WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ------------------------------------------------------------------------------
# 3. Home Page: Book Search
# ------------------------------------------------------------------------------
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = None
    books = []

    if request.method == 'POST':
        query = request.form['query']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM "books"
            WHERE isbn ILIKE %s OR title ILIKE %s OR author ILIKE %s
        """, ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        books = cur.fetchall()
        cur.close()
        conn.close()

    return render_template('home.html', books=books, query=query)


# ------------------------------------------------------------------------------
# 4. Book Details: Show Book Info + Existing Reviews
# ------------------------------------------------------------------------------
@app.route('/book_details/<search>', methods=['GET'])
def book_details(search):
    """Displays details for the first matching book and any existing reviews."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Find the book by ISBN, title, or author
    cur.execute("""
        SELECT * FROM "books"
        WHERE isbn ILIKE %s OR title ILIKE %s OR author ILIKE %s
    """, ('%' + search + '%', '%' + search + '%', '%' + search + '%'))
    book = cur.fetchone()

    if not book:
        cur.close()
        conn.close()
        flash('No book found matching your search!', 'danger')
        return redirect(url_for('home'))

    # book[0] is the isbn because the order is: (isbn, title, author, year)
    isbn = book[0]

    # Retrieve existing reviews for this book
    cur.execute('''
        SELECT r.rating, r.review_text, r.created_at, u.username
        FROM "Reviews" r
        JOIN "Users" u ON r.user_id = u.id
        WHERE r.book_isbn = %s
        ORDER BY r.created_at DESC
    ''', (isbn,))
    reviews = cur.fetchall()

    cur.close()
    conn.close()

    # Pass both book and reviews to the template
    return render_template('book_details.html', book=book, reviews=reviews)


# ------------------------------------------------------------------------------
# 5. Submit a Review
# ------------------------------------------------------------------------------
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        flash('You must be logged in to submit a review.', 'danger')
        return redirect(url_for('login'))

    # Get form data
    book_isbn = request.form.get('book_isbn')  # Hidden <input> in your HTML
    rating = request.form.get('rating')
    review_text = request.form.get('review_text')

    if not (book_isbn and rating and review_text):
        flash("All fields are required.", "danger")
        return redirect(url_for('book_details', search=book_isbn))

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash("Rating must be a number between 1 and 5.", "danger")
            return redirect(url_for('book_details', search=book_isbn))
    except ValueError:
        flash("Rating must be a number between 1 and 5.", "danger")
        return redirect(url_for('book_details', search=book_isbn))

    user_id = session['user_id']

    # Check if the user already reviewed this book
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM "Reviews" WHERE user_id = %s AND book_isbn = %s', 
                (user_id, book_isbn))
    existing_review = cur.fetchone()

    if existing_review:
        flash("You have already submitted a review for this book.", "warning")
        cur.close()
        conn.close()
        return redirect(url_for('book_details', search=book_isbn))

    # Insert new review
    cur.execute('''
        INSERT INTO "Reviews" (user_id, book_isbn, rating, review_text)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, book_isbn, rating, review_text))
    conn.commit()

    cur.close()
    conn.close()

    flash("Review submitted successfully!", "success")
    return redirect(url_for('book_details', search=book_isbn))

# ------------------------------------------------------------------------------
# 6. Run the App
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    create_reviews_table_if_not_exists()
    app.run(debug=True)
