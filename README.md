# Project 1 + 2
Here under the templates I have created 4 .html files for the frondend:
Registration File for registration page
Login for Login Page
Home is for Book Search and also a with logout button
Book_details is for the result of search which will show book details, 

Then in routes.py file, I have created routes for these pages, what this code is doing is:
1. It has app initalization
2. Creating a database connection
3. Setting a route for registration
4. Checks id password and confirmation matches
5. Checks if user already exists
6. Setting a route for login
7. Setting a route for Home page
8. Setting a route for Book_details page
9. Setting a route for logout
10. Review Submission – Users can submit a review (rating 1–5 and text). Enforces one review per user per book.
11. Google Books API Integration – Fetches average rating, ratings count, and description from the Google Books API for each book.
12. Gemini API Integration – Summarizes the book’s description into fewer than 50 words.
13. /api/<isbn> Route – Returns a JSON response containing the book’s title, author, published date, ISBN (both ISBN_10 and ISBN_13), review count, average rating, full description (from Google Books), and summarized description (from Gemini). If the ISBN is not in the local database, returns a 404 error.

Then we have import.py file
In this file I have created databse connection
Then wrote a code to create a table
It reads data from csv file (books.csv) and insert into database

In summary.py File, I have implemented:

Environment Variable for API Key – Retrieves the Gemini API key (GEMINI_API_KEY) from environment variables.
summarize_with_gemini(description) Function – It sends a POST request to Google’s Gemini 1.5 Flash API to summarize the given description text to fewer than 50 words.
Error Handling – If there’s an issue with the request or the API key is missing, returns None instead of a summary.
