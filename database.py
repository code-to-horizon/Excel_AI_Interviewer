# database.py
import sqlite3
import datetime
import json

def init_db():
    """Initializes the database and creates the candidates table if it doesn't exist."""
    conn = sqlite3.connect('candidates.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            userid TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid TEXT NOT NULL,
            interview_timestamp TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            max_score INTEGER NOT NULL,
            final_percentage REAL NOT NULL,
            warning_count INTEGER NOT NULL,
            detailed_results TEXT,
            FOREIGN KEY (userid) REFERENCES candidates (userid)
        )
    ''')
    # Check if the table is empty to add sample data once
    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        add_sample_data(cursor)
    
    conn.commit()
    conn.close()

def save_interview_results(userid, evaluations, warning_count):
    """Calculates and saves the final interview results to the database."""
    if not evaluations:
        return

    total_score = sum(item.get('score', 0) for item in evaluations)
    max_score = len(evaluations) * 5  # Assuming each question is out of 5
    final_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    detailed_results_json = json.dumps(evaluations)
    timestamp = datetime.datetime.now().isoformat()

    conn = sqlite3.connect('candidates.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interview_results (userid, interview_timestamp, total_score, max_score, final_percentage, warning_count, detailed_results)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (userid, timestamp, total_score, max_score, final_percentage, warning_count, detailed_results_json))
    
    conn.commit()
    conn.close()
    print(f"Results for user {userid} saved successfully.")

def add_sample_data(cursor):
    """Adds a few sample candidates to the database for testing."""
    sample_users = [
        ('priya_s', 'pass123', 'Priya Sharma', 'priya.s@example.com'),
        ('amit_k', 'pass456', 'Amit Kumar', 'amit.k@example.com'),
        ('sneha_p', 'pass789', 'Sneha Patel', 'sneha.p@example.com')
    ]
    cursor.executemany("INSERT INTO candidates VALUES (?, ?, ?, ?)", sample_users)
    print("Sample data added to the database.")

def verify_user(userid, password):
    """Verifies user credentials against the database."""
    conn = sqlite3.connect('candidates.db')
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM candidates WHERE userid = ? AND password = ?", (userid, password))
    user_data = cursor.fetchone()
    
    conn.close()
    
    if user_data:
        return dict(user_data) # Return user data as a dictionary
    return None