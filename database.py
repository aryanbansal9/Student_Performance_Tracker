# database.py
#
# This file is the ONLY place in our project that talks to SQLite.
# Every other file (app.py, models.py) goes THROUGH this file to
# read or write data. This is called a "data access layer" —
# if we ever switch from SQLite to MySQL/Postgres later, we only
# need to change THIS file, not the whole app.
#
# SQLite stores everything in a single file (student_tracker.db).
# No server, no installation — perfect for learning and small apps.

import sqlite3
from models import Student

DB_NAME = "student_tracker.db"


def get_connection():
    """
    Opens a connection to the SQLite database file.
    If the file doesn't exist yet, SQLite creates it automatically.

    row_factory = sqlite3.Row lets us access columns by NAME
    (like row["name"]) instead of by position (like row[1]),
    which makes the code much easier to read.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the database tables if they don't already exist.
    Run this once when the app starts.

    We use TWO tables:

    1. students        -> one row per student
       roll_number (TEXT, PRIMARY KEY) | name (TEXT)

    2. grades           -> one row per (student, subject) grade
       roll_number (TEXT) | subject (TEXT) | score (INTEGER)

    Why two tables instead of storing grades as a dict in one
    column? Because SQL is "relational" — it's built around
    rows and columns, not nested data. Splitting grades into
    their own table lets us easily query things like
    "average score for Math across all students" using SQL
    itself, which is much faster than loading everything into
    Python and looping.

    FOREIGN KEY links grades.roll_number to students.roll_number.
    ON DELETE CASCADE means: if a student is deleted, all their
    grade rows are automatically deleted too — no orphaned data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_number TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
                ON DELETE CASCADE,
            UNIQUE (roll_number, subject)
        )
    """)

    # UNIQUE (roll_number, subject) means a student can only have
    # ONE grade per subject. If we add "Math" again for the same
    # student, we will UPDATE the existing row instead of creating
    # a duplicate. We handle that with "INSERT OR REPLACE" below.

    conn.commit()
    conn.close()


# ── STUDENT OPERATIONS ──────────────────────────────────────

def db_add_student(roll_number, name):
    """
    Inserts a new student row.
    Returns (success, message).
    """
    roll_number = str(roll_number).strip()
    name = name.strip()

    if not roll_number or not name:
        return False, "Roll number and name cannot be empty."

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO students (roll_number, name) VALUES (?, ?)",
            (roll_number, name)
        )
        conn.commit()
        return True, f"Student '{name}' added successfully."

    except sqlite3.IntegrityError:
        # IntegrityError fires because roll_number is PRIMARY KEY
        # and a row with this value already exists.
        return False, f"A student with roll number {roll_number} already exists."

    finally:
        # finally ALWAYS runs, whether we returned True or False
        # above. This guarantees we never leave a connection open,
        # even if something goes wrong.
        conn.close()


def db_get_student(roll_number):
    """
    Fetches ONE student (with their grades) as a Student object.
    Returns None if not found.
    """
    roll_number = str(roll_number).strip()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT roll_number, name FROM students WHERE roll_number = ?",
        (roll_number,)
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    # Now fetch all grades for this student
    cursor.execute(
        "SELECT subject, score FROM grades WHERE roll_number = ?",
        (roll_number,)
    )
    grade_rows = cursor.fetchall()
    conn.close()

    # Build a {subject: score} dict from the grade rows
    grades = {g["subject"]: g["score"] for g in grade_rows}

    return Student(row["roll_number"], row["name"], grades)


def db_get_all_students():
    """
    Fetches ALL students with their grades, sorted by roll number.
    Returns a list of Student objects.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT roll_number, name FROM students ORDER BY roll_number")
    student_rows = cursor.fetchall()

    cursor.execute("SELECT roll_number, subject, score FROM grades")
    grade_rows = cursor.fetchall()
    conn.close()

    # Group grades by roll_number so we can attach them to the
    # right student. This avoids running a separate query per
    # student (which would be slow with many students — a problem
    # known as the "N+1 query problem").
    grades_by_student = {}
    for g in grade_rows:
        roll = g["roll_number"]
        grades_by_student.setdefault(roll, {})[g["subject"]] = g["score"]

    students = []
    for row in student_rows:
        grades = grades_by_student.get(row["roll_number"], {})
        students.append(Student(row["roll_number"], row["name"], grades))

    return students


def db_delete_student(roll_number):
    """
    Deletes a student (and their grades, via ON DELETE CASCADE).
    Returns (success, message).
    """
    roll_number = str(roll_number).strip()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE roll_number = ?", (roll_number,))
    deleted_count = cursor.rowcount  # how many rows were actually deleted

    conn.commit()
    conn.close()

    if deleted_count == 0:
        return False, f"No student found with roll number {roll_number}."

    return True, "Student deleted successfully."


# ── GRADE OPERATIONS ─────────────────────────────────────────

def db_add_grade(roll_number, subject, score):
    """
    Adds (or updates) a grade for a student.
    Returns (success, message).
    """
    roll_number = str(roll_number).strip()
    subject = subject.strip()

    # Validate score range BEFORE touching the database
    if not (0 <= score <= 100):
        return False, "Score must be between 0 and 100."

    if not subject:
        return False, "Subject name cannot be empty."

    conn = get_connection()
    cursor = conn.cursor()

    # Check the student exists first — gives a clearer error
    # message than a generic foreign key failure.
    cursor.execute("SELECT name FROM students WHERE roll_number = ?", (roll_number,))
    student_row = cursor.fetchone()

    if student_row is None:
        conn.close()
        return False, f"No student found with roll number {roll_number}."

    # INSERT OR REPLACE: if (roll_number, subject) already exists
    # (remember our UNIQUE constraint), this UPDATES the score
    # instead of creating a duplicate row.
    cursor.execute("""
        INSERT OR REPLACE INTO grades (roll_number, subject, score)
        VALUES (?, ?, ?)
    """, (roll_number, subject, score))

    conn.commit()
    conn.close()

    return True, f"Grade added: {subject} = {score} for {student_row['name']}."


# ── BONUS FEATURE QUERIES ────────────────────────────────────

def db_subject_topper(subject):
    """
    Returns (name, roll_number, score) for the highest scorer
    in a subject, or None if nobody has a grade for it.

    Notice how SQL does the "find the max" work for us with
    ORDER BY ... DESC LIMIT 1 — we don't need to loop in Python.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.name, s.roll_number, g.score
        FROM grades g
        JOIN students s ON g.roll_number = s.roll_number
        WHERE g.subject = ?
        ORDER BY g.score DESC
        LIMIT 1
    """, (subject,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row["name"], row["roll_number"], row["score"]


def db_class_average(subject):
    """
    Returns the average score for a subject across all students,
    or None if nobody has a grade for it.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(score) as avg_score, COUNT(*) as count
        FROM grades
        WHERE subject = ?
    """, (subject,))

    row = cursor.fetchone()
    conn.close()

    if row["count"] == 0:
        return None

    return round(row["avg_score"], 2)


def db_get_all_subjects():
    """
    Returns a sorted list of every distinct subject that has
    at least one grade entered. Used to populate dropdowns
    in the HTML forms.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT subject FROM grades ORDER BY subject")
    rows = cursor.fetchall()
    conn.close()

    return [row["subject"] for row in rows]