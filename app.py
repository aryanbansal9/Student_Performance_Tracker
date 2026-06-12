# app.py
#
# This is the Flask application — the "web" part of our project.
# Flask's job: when a browser visits a URL (a "route"), run a
# Python function and return an HTML page.
#
# We deliberately keep this file THIN. All the real logic lives
# in database.py and models.py. app.py just:
#   1. Reads form data from the request
#   2. Calls the right database function
#   3. Decides which HTML template to show, and with what data
#
# This separation means if we ever build a second interface
# (say, a command-line version, or a mobile app), we can reuse
# database.py and models.py without rewriting any logic.

from flask import Flask, render_template, request, redirect, url_for, flash
from database import (
    init_db,
    db_add_student,
    db_get_student,
    db_get_all_students,
    db_delete_student,
    db_add_grade,
    db_subject_topper,
    db_class_average,
    db_get_all_subjects,
)

app = Flask(__name__)

# secret_key is required for "flash" messages (the little
# success/error banners). In a real production app this should
# be a long random string stored as an environment variable —
# we'll cover that in the deployment step. For local learning,
# a simple string is fine.
app.secret_key = "student-tracker-secret-key-change-in-production"


# Run init_db() once when the app starts, so the tables exist
# before any request comes in.
init_db()


# ── HOME PAGE: list all students ────────────────────────────

@app.route("/")
def index():
    """
    Shows the dashboard: every student, their average, and
    quick links to view/add grades or delete them.
    """
    students = db_get_all_students()

    # Convert each Student object to a dict so the template
    # can easily access .name, .roll_number, .grades, .average
    students_data = [s.to_dict() for s in students]

    return render_template("index.html", students=students_data)


# ── ADD STUDENT ──────────────────────────────────────────────

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    """
    GET  -> show the "add student" form
    POST -> the form was submitted, try to add the student
    """
    if request.method == "POST":
        roll_number = request.form.get("roll_number", "")
        name = request.form.get("name", "")

        success, message = db_add_student(roll_number, name)

        # flash() stores a one-time message that we display on
        # the NEXT page. "success"/"error" are categories we use
        # to colour the message differently in the template.
        flash(message, "success" if success else "error")

        if success:
            # redirect() sends the browser to a NEW url (the home
            # page). This is important: if we just rendered the
            # home page directly here, refreshing the browser
            # would re-submit the form and add the student again.
            # Redirecting avoids that ("Post/Redirect/Get" pattern).
            return redirect(url_for("index"))

        # If it failed, show the form again so they can fix it
        return render_template("add_student.html")

    # GET request -> just show the empty form
    return render_template("add_student.html")


# ── ADD GRADE ────────────────────────────────────────────────

@app.route("/add_grade", methods=["GET", "POST"])
def add_grade():
    """
    GET  -> show the "add grade" form (with a student dropdown)
    POST -> the form was submitted, try to add the grade
    """
    students = db_get_all_students()
    students_data = [s.to_dict() for s in students]

    if request.method == "POST":
        roll_number = request.form.get("roll_number", "")
        subject = request.form.get("subject", "")
        score_input = request.form.get("score", "")

        # Validate the score is a whole number BEFORE calling
        # the database function. This catches things like
        # someone typing "abc" into the score field.
        try:
            score = int(score_input)
        except ValueError:
            flash("Score must be a whole number.", "error")
            return render_template("add_grade.html", students=students_data)

        success, message = db_add_grade(roll_number, subject, score)
        flash(message, "success" if success else "error")

        if success:
            return redirect(url_for("index"))

        return render_template("add_grade.html", students=students_data)

    return render_template("add_grade.html", students=students_data)


# ── STUDENT DETAIL PAGE ──────────────────────────────────────

@app.route("/student/<roll_number>")
def student_detail(roll_number):
    """
    Shows full details for ONE student: name, roll number,
    every grade, and their average.

    <roll_number> in the route is a "variable" — whatever the
    user puts in the URL (e.g. /student/101) gets passed into
    this function as the roll_number argument.
    """
    student = db_get_student(roll_number)

    if student is None:
        flash(f"No student found with roll number {roll_number}.", "error")
        return redirect(url_for("index"))

    return render_template("student_detail.html", student=student.to_dict())


# ── DELETE STUDENT ───────────────────────────────────────────

@app.route("/delete_student/<roll_number>", methods=["POST"])
def delete_student(roll_number):
    """
    Deletes a student. We only allow POST (not GET) for delete
    actions — this is a security best practice. GET requests can
    be triggered accidentally (e.g. by a browser pre-fetching
    links, or a search engine crawler), but POST requires an
    actual form submission.
    """
    success, message = db_delete_student(roll_number)
    flash(message, "success" if success else "error")
    return redirect(url_for("index"))


# ── BONUS: SUBJECT INSIGHTS PAGE ────────────────────────────

@app.route("/insights", methods=["GET", "POST"])
def insights():
    """
    Bonus feature page: pick a subject, see the topper and
    class average for that subject.
    """
    subjects = db_get_all_subjects()
    result = None
    selected_subject = None

    if request.method == "POST":
        selected_subject = request.form.get("subject", "").strip()

        # Guard against an empty selection. This can happen if
        # someone submits the form without choosing an option
        # (e.g. the placeholder "-- Select a subject --" was sent,
        # or the request was made without a browser at all).
        if not selected_subject:
            flash("Please choose a subject from the list.", "error")
            return render_template(
                "insights.html",
                subjects=subjects,
                result=None,
                selected_subject=None,
            )

        topper = db_subject_topper(selected_subject)
        avg = db_class_average(selected_subject)

        if topper is None:
            flash(f"No grades found yet for '{selected_subject}'.", "error")
        else:
            topper_name, topper_roll, topper_score = topper
            result = {
                "subject": selected_subject,
                "topper_name": topper_name,
                "topper_roll": topper_roll,
                "topper_score": topper_score,
                "class_average": avg,
            }

    return render_template(
        "insights.html",
        subjects=subjects,
        result=result,
        selected_subject=selected_subject,
    )


# ── RUN THE APP ──────────────────────────────────────────────

if __name__ == "__main__":
    # debug=True gives us:
    #  - Detailed error pages in the browser (instead of a
    #    generic "500 Internal Server Error")
    #  - Auto-reload: the server restarts automatically when
    #    we save a code change
    #
    # IMPORTANT: debug=True must be turned OFF (or removed)
    # before deploying to a live server — it can leak sensitive
    # information to anyone who visits the site. We'll handle
    # this properly in the deployment step.
    app.run(debug=True)