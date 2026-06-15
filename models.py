"""Domain models for the Student Performance Tracker.

These classes represent students and the operations available on
them, independent of how the data is persisted.
"""


class Student:
    """A single student and their subject-wise scores."""

    def __init__(self, roll_no, name, scores=None):
        self.roll_no = roll_no
        self.name = name
        self.scores = scores if scores is not None else {}

    def set_score(self, subject, value):
        """Record a score for a subject. Returns False if out of range."""
        if not (0 <= value <= 100):
            return False
        self.scores[subject] = value
        return True

    def average(self):
        if not self.scores:
            return 0
        return round(sum(self.scores.values()) / len(self.scores), 2)

    def as_dict(self):
        return {
            "roll_no": self.roll_no,
            "name": self.name,
            "scores": self.scores,
            "average": self.average(),
        }

    def __repr__(self):
        return f"Student({self.roll_no!r}, {self.name!r}, {self.scores})"


