import sqlite3

DB_NAME = "feedback.db"

def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        favourite_book TEXT NOT NULL,
        recommended_book TEXT NOT NULL,
        genre TEXT,
        mood TEXT,
        pace TEXT,
        length TEXT,        
        features TEXT NOT NULL,
        label INTEGER NOT NULL 
        )
        """)
    connection.commit()
    connection.close()

def insert_feedback(
    favourite_book,
    recommended_book,
    genre,
    mood,
    pace,
    length,
    features,
    label
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO feedback (
            favourite_book,
            recommended_book,
            genre,
            mood,
            pace,
            length,
            features,
            label
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        favourite_book,
        recommended_book,
        genre,
        mood,
        pace,
        length,
        features,
        label
    ))

    connection.commit()
    connection.close()

def fetch_feedback():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT features, label FROM feedback
    """)

    rows = cursor.fetchall()
    connection.close()

    return rows

def get_label_distribution():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT label, COUNT(*) as count
        FROM feedback
        GROUP BY label
    """)
    
    result = cursor.fetchall()
    connection.close()

    return {row["label"]: row["count"] for row in result}

    