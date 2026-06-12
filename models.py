# models.py
#
# This file defines the "blueprint" classes for our app.
# Think of a class as a template — Student is the template for
# "what does one student look like in our system?"
#
# We are NOT touching the database here. This file only knows
# about Python objects in memory. The database file (database.py)
# will be responsible for saving/loading these objects.
#
# Keeping these separate is a common pattern called
# "separation of concerns" — each file has ONE job.


class Student:
    """
    Represents a single student.

    Attributes:
        roll_number (str): Unique ID for the student (e.g. "101")
        name (str): Student's full name
        grades (dict): Subject -> score, e.g. {"Math": 85, "Science": 90}
    """

    def __init__(self, roll_number, name, grades=None):
        self.roll_number = roll_number
        self.name = name

        # IMPORTANT: never use a mutable default like grades={}
        # directly in the function signature. If you did, every
        # Student object would SHARE the same dictionary by
        # accident. Instead we check for None and create a fresh
        # dict here.
        self.grades = grades if grades is not None else {}

    def add_grade(self, subject, score):
        """
        Adds or updates a grade for a subject.
        Returns True if successful, False if the score is invalid.
        """
        # Validate the score is within a sensible range
        if not (0 <= score <= 100):
            return False

        self.grades[subject] = score
        return True

    def calculate_average(self):
        """
        Returns the average of all grades.
        If the student has no grades yet, returns 0 instead of
        crashing with a divide-by-zero error.
        """
        if not self.grades:
            return 0

        total = sum(self.grades.values())
        count = len(self.grades)
        return round(total / count, 2)

    def to_dict(self):
        """
        Converts this Student object into a plain dictionary.
        Useful for saving to JSON or passing to HTML templates.
        """
        return {
            "roll_number": self.roll_number,
            "name": self.name,
            "grades": self.grades,
            "average": self.calculate_average(),
        }

    def __repr__(self):
        # __repr__ controls how the object looks when printed.
        # This is purely for debugging — helps us "see" the object
        # when we print it in the terminal.
        return f"Student(roll_number={self.roll_number!r}, name={self.name!r}, grades={self.grades})"


class StudentTracker:
    """
    Manages a collection of Student objects.

    This class doesn't know HOW students are stored long-term
    (that's database.py's job). It only manages the students
    that are currently loaded in memory, and provides methods
    to search, add, and analyse them.
    """

    def __init__(self):
        # We store students in a dictionary keyed by roll_number.
        # Why a dict instead of a list?
        # -> Looking up a student by roll number becomes instant
        #    (O(1)) instead of having to loop through a list (O(n)).
        self.students = {}

    def add_student(self, roll_number, name):
        """
        Adds a new student. Returns (success, message) so the
        caller (Flask route) can show useful feedback.
        """
        roll_number = str(roll_number).strip()
        name = name.strip()

        if not roll_number or not name:
            return False, "Roll number and name cannot be empty."

        if roll_number in self.students:
            return False, f"A student with roll number {roll_number} already exists."

        self.students[roll_number] = Student(roll_number, name)
        return True, f"Student '{name}' added successfully."

    def get_student(self, roll_number):
        """
        Returns the Student object for a roll number, or None
        if it doesn't exist. Using .get() instead of [] avoids
        a KeyError crash if the roll number isn't found.
        """
        return self.students.get(str(roll_number).strip())

    def add_grade(self, roll_number, subject, score):
        """
        Adds a grade to a specific student.
        Returns (success, message).
        """
        student = self.get_student(roll_number)

        if student is None:
            return False, f"No student found with roll number {roll_number}."

        if not subject.strip():
            return False, "Subject name cannot be empty."

        success = student.add_grade(subject.strip(), score)

        if not success:
            return False, "Score must be between 0 and 100."

        return True, f"Grade added: {subject} = {score} for {student.name}."

    def get_all_students(self):
        """
        Returns a list of all students as dictionaries.
        Sorted by roll number so the order is predictable
        (dictionaries don't guarantee order across reloads).
        """
        return [s.to_dict() for s in sorted(
            self.students.values(),
            key=lambda s: s.roll_number
        )]

    def subject_topper(self, subject):
        """
        Bonus feature: finds the student with the highest score
        in a given subject.

        Returns the Student object, or None if no one has a
        grade for that subject.
        """
        best_student = None
        best_score = -1  # start lower than any possible score (0-100)

        for student in self.students.values():
            if subject in student.grades:
                score = student.grades[subject]
                if score > best_score:
                    best_score = score
                    best_student = student

        # If nobody has a grade for this subject, return a single
        # None (not a tuple) so the caller can do:
        #     result = tracker.subject_topper("Math")
        #     if result is None: ...
        # Without this check, "return best_student, best_score"
        # would always return a 2-item tuple like (None, -1),
        # which is truthy and would slip past an `if result:` check.
        if best_student is None:
            return None

        return best_student, best_score

    def class_average(self, subject):
        """
        Bonus feature: average score for the WHOLE class in
        one subject.

        Returns None if no student has a grade for that subject
        (so we don't divide by zero).
        """
        scores = [
            student.grades[subject]
            for student in self.students.values()
            if subject in student.grades
        ]

        if not scores:
            return None

        return round(sum(scores) / len(scores), 2)