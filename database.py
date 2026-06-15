import csv
import io
import sqlite3
from datetime import datetime
from models import Student

class StudentTracker:
    def __init__(self, db_path="student_tracker.db"):
        self.db_path = db_path
        self._init_db()

    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    roll_no TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL REFERENCES students(roll_no) ON DELETE CASCADE,
                    subject TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    UNIQUE (roll_no, subject)
                )
            """)

    def enroll_student(self, roll_no, name):
        roll_no = str(roll_no).strip()
        name = name.strip()
        
        if not roll_no or not name:
            return False, "Roll number and name are required."

        try:
            with self.get_db() as conn:
                conn.execute(
                    "INSERT INTO students (roll_no, name) VALUES (?, ?)",
                    (roll_no, name),
                )
            return True, f"{name} enrolled successfully."
        except sqlite3.IntegrityError:
            return False, f"Roll number {roll_no} is already in use."

    def get_student(self, roll_no):
        roll_no = str(roll_no).strip()
        with self.get_db() as conn:
            row = conn.execute(
                "SELECT roll_no, name FROM students WHERE roll_no = ?", (roll_no,)
            ).fetchone()
            
            if not row:
                return None

            scores = conn.execute(
                "SELECT subject, value FROM scores WHERE roll_no = ?", (roll_no,)
            ).fetchall()

        return Student(row["roll_no"], row["name"], {r["subject"]: r["value"] for r in scores})

    def list_students(self):
        with self.get_db() as conn:
            students = conn.execute("SELECT roll_no, name FROM students ORDER BY roll_no").fetchall()
            scores = conn.execute("SELECT roll_no, subject, value FROM scores").fetchall()

        by_roll = {}
        for row in scores:
            by_roll.setdefault(row["roll_no"], {})[row["subject"]] = row["value"]

        return [
            Student(row["roll_no"], row["name"], by_roll.get(row["roll_no"], {}))
            for row in students
        ]

    def remove_student(self, roll_no):
        roll_no = str(roll_no).strip()
        with self.get_db() as conn:
            cur = conn.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))

        if cur.rowcount == 0:
            return False, f"No student found with roll number {roll_no}."
        return True, "Student removed successfully."

    def record_score(self, roll_no, subject, value):
        roll_no, subject = str(roll_no).strip(), subject.strip()

        if not (0 <= value <= 100):
            return False, "Score must be between 0 and 100."
        if not subject:
            return False, "Subject is required."

        with self.get_db() as conn:
            student = conn.execute("SELECT name FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
            if not student:
                return False, f"No student found with roll number {roll_no}."

            conn.execute(
                """INSERT INTO scores (roll_no, subject, value) VALUES (?, ?, ?)
                   ON CONFLICT(roll_no, subject) DO UPDATE SET value = excluded.value""",
                (roll_no, subject, value),
            )

        return True, f"{subject} = {value} recorded for {student['name']}."

    def list_subjects(self):
        with self.get_db() as conn:
            rows = conn.execute("SELECT DISTINCT subject FROM scores ORDER BY subject").fetchall()
        return [r["subject"] for r in rows]

    def subject_topper(self, subject):
        with self.get_db() as conn:
            row = conn.execute(
                """SELECT s.name, s.roll_no, sc.value
                   FROM scores sc JOIN students s ON sc.roll_no = s.roll_no
                   WHERE sc.subject = ?
                   ORDER BY sc.value DESC LIMIT 1""",
                (subject,),
            ).fetchone()

        return (row["name"], row["roll_no"], row["value"]) if row else None

    def subject_average(self, subject):
        with self.get_db() as conn:
            row = conn.execute(
                "SELECT AVG(value) AS avg_value, COUNT(*) AS n FROM scores WHERE subject = ?",
                (subject,),
            ).fetchone()

        return round(row["avg_value"], 2) if row["n"] else None

    def export_csv(self):
        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT s.roll_no, s.name, sc.subject, sc.value
                FROM students s
                LEFT JOIN scores sc ON s.roll_no = sc.roll_no
                ORDER BY s.roll_no, sc.subject
            """).fetchall()

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["roll_no", "name", "subject", "score"])

        for row in rows:
            writer.writerow([row["roll_no"], row["name"], row["subject"] or "", row["value"] if row["value"] is not None else ""])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tracker_backup_{timestamp}.csv", buffer.getvalue()