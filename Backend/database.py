import sqlite3
from datetime import datetime


DATABASE_FILE = "Backend/muba.db"


def get_connection():
    return sqlite3.connect(DATABASE_FILE)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    # ============================================================
    # QUIZZES
    # ============================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            student_level TEXT NOT NULL,
            language TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            num_questions INTEGER NOT NULL,
            questions TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ============================================================
    # STUDENT ATTEMPTS
    # ============================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            answers TEXT NOT NULL,
            questions TEXT,
            score INTEGER,
            total_questions INTEGER,
            submitted_at TEXT NOT NULL,
            attempt_type TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    """)

    # Add the questions column to existing databases.
    # This keeps old student attempts instead of deleting them.
    cursor.execute("""
        PRAGMA table_info(student_attempts)
    """)

    columns = [row[1] for row in cursor.fetchall()]

    if "questions" not in columns:
        cursor.execute("""
            ALTER TABLE student_attempts
            ADD COLUMN questions TEXT
        """)

    if "student_id" not in columns:
        cursor.execute("""
            ALTER TABLE student_attempts
            ADD COLUMN student_id TEXT
        """)

    # ============================================================
    # AI ANALYSES
    # ============================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    """)

    connection.commit()
    connection.close()