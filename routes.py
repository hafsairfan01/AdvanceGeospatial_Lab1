from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from summary import summarize_with_gemini

import psycopg2

### GOOGLE BOOKS INTEGRATION ###
import requests
###GEMINI API INTEGRATION###
from dotenv import load_dotenv
load_dotenv()  # loads variables from .env into os.environ

import os
gemini_key = os.environ.get("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = 'fgfgfgf uidihhchh'

# ------------------------------------------------------------------------------
# Database Connection & Setup
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

def create_tables_if_not_exists():
    """Ensures the necessary tables exist with correct columns/constraints."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Users" (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)

    # Books table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "books" (
            isbn VARCHAR(20) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            year INTEGER
        );
    """)

    # Reviews table
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
#-------------------------------------------------------------------------
### GOOGLE BOOKS INTEGRATION ###
#---------------------------------------------------------------------------
def get_google_books_info(isbn):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"isbn:{isbn}"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        items = data.get('items', [])
        if not items:
            return None

        volume_info = items[0].get('volumeInfo', {})
        average_rating = volume_info.get('averageRating')
        ratings_count = volume_info.get('ratingsCount')
        description   = volume_info.get('description')


        # 1) Parse industryIdentifiers for ISBN_10 and ISBN_13
        industry_ids = volume_info.get('industryIdentifiers', [])
        isbn_10 = None
        isbn_13 = None
        for identifier in industry_ids:
            t = identifier.get('type')      # e.g. "ISBN_10" or "ISBN_13"
            val = identifier.get('identifier')
            if t == "ISBN_10":
                isbn_10 = val
            elif t == "ISBN_13":
                isbn_13 = val

        # 2) Return the extended dictionary with ISBN_10 and ISBN_13
        return {
            "average_rating": average_rating,
            "ratings_count": ratings_count,
            "description": description,
            "isbn_10": isbn_10,
            "isbn_13": isbn_13
        }
    except (requests.RequestException, ValueError):
        return None

#------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Registration
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

       
        cur.execute('INSERT INTO "Users" (username, password) VALUES (%s, %s)',
                    (username, password))
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------------------------------------------------------------------
# Login
# ------------------------------------------------------------------------------
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

        if user and user[2] == password:
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')


# ------------------------------------------------------------------------------
# Logout
# ------------------------------------------------------------------------------
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ------------------------------------------------------------------------------
# Home (Book Search)
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
# Book Details + Show Local and Google Ratings
# ------------------------------------------------------------------------------
@app.route('/book_details/<search>', methods=['GET'])
def book_details(search):
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Look up local book by partial ISBN, title, or author
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

    # 2) Retrieve local reviews
    isbn = book[0]
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

    # 3) Get Google Books info, including the description
    google_data = get_google_books_info(isbn)
    google_avg = None
    google_count = None
    google_desc = None

    if google_data:
        google_avg = google_data["average_rating"]
        google_count = google_data["ratings_count"]
        google_desc = google_data["description"]

    # 4) Summarize the description with Gemini
    gemini_summary = None
    if google_desc:
        gemini_summary = summarize_with_gemini(google_desc)

    # 5) Render the template with local + Google data + Gemini summary
    return render_template(
        'book_details.html',
        book=book,
        reviews=reviews,
        google_avg=google_avg,
        google_count=google_count,
        gemini_summary=gemini_summary
    )


# ------------------------------------------------------------------------------
# Submit a Review
# ------------------------------------------------------------------------------
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        flash('You must be logged in to submit a review.', 'danger')
        return redirect(url_for('login'))

    book_isbn = request.form.get('book_isbn')
    rating = request.form.get('rating')
    review_text = request.form.get('review_text')

    if not (book_isbn and rating and review_text):
        flash("All fields are required.", "danger")
        return redirect(url_for('book_details', search=book_isbn))

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.", "danger")
            return redirect(url_for('book_details', search=book_isbn))
    except ValueError:
        flash("Rating must be a valid integer.", "danger")
        return redirect(url_for('book_details', search=book_isbn))

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if review already exists
    cur.execute('''
        SELECT * FROM "Reviews"
        WHERE user_id = %s AND book_isbn = %s
    ''', (user_id, book_isbn))
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

#-------------------------------------------------------------------------------
# Website’s /api/<isbn> Route
#-------------------------------------------------------------------------------
@app.route("/api/<isbn>", methods=["GET"])
def book_api(isbn):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Check if book is in our local DB
    cur.execute("""SELECT isbn, title, author, year 
                   FROM "books" 
                   WHERE isbn = %s""", (isbn,))
    book = cur.fetchone()

    if not book:
        cur.close()
        conn.close()
        return jsonify({"error": "Book not found"}), 404

    # 2) Gather local reviews info
    cur.execute("""SELECT rating FROM "Reviews" WHERE book_isbn = %s""", (isbn,))
    reviews_data = cur.fetchall()
    review_count = len(reviews_data)
    average_rating = sum(r[0] for r in reviews_data) / review_count if review_count else 0

    # 3) Get Google Books info + ISBN_10, ISBN_13, description, etc.
    google_info = get_google_books_info(isbn)
    if google_info:
        description = google_info.get("description")
        isbn_10 = google_info.get("isbn_10")
        isbn_13 = google_info.get("isbn_13")
    else:
        description = None
        isbn_10 = None
        isbn_13 = None

    # 4) Summarize description using Gemini
    if description:
        summarized_desc = summarize_with_gemini(description)
    else:
        summarized_desc = None

    # 5) Build the JSON response
    response_data = {
        "title": book[1],
        "author": book[2],
        "published_date": book[3],
        "isbn_10": isbn_10,
        "isbn_13": isbn_13,
        "review_count": review_count,
        "average_rating": average_rating,
        "description": description,
        "summarized_description": summarized_desc
    }

    cur.close()
    conn.close()

    return jsonify(response_data)


# ------------------------------------------------------------------------------
# Run the App
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    create_tables_if_not_exists()
    app.run(debug=True)
