import csv
import psycopg2
from psycopg2 import sql

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",  
        database="Lab_01_database",  
        user="postgres",  
        password="123"  
    )
    return conn

# Create the table if it doesn't exist
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create the books table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            isbn VARCHAR(20) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            year INTEGER
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# Function to import books from CSV file into PostgreSQL
def import_books_from_csv(csv_file):
    conn = get_db_connection()
    cur = conn.cursor()  
    
    try:
        # Open the CSV file and read its contents
        with open(csv_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Insert each book record into the PostgreSQL table
                cur.execute("""
                    INSERT INTO books (isbn, title, author, year)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (isbn) DO NOTHING;
                """, (row['isbn'], row['title'], row['author'], row['year']))
        
        conn.commit()
    except FileNotFoundError as e:
        print(f"Error: The file {csv_file} was not found. Please check the file path.")
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()  
        conn.close()  

if __name__ == "__main__":
    # Create the table if it doesn't exist
    create_table()

    # Import books from the CSV file 
    import_books_from_csv('C:/Users/HafsaIrfan/Documents/GitHub/AdvanceGeospatial_Lab01/AdvanceGeospatial_Lab1/books.csv')

    print("Books imported successfully!")
