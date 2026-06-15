import os
from flask import Flask, Response, flash, redirect, render_template, request, url_for
from database import StudentTracker

app = Flask(__name__)
# In a real app, this would be an environment variable. For now, a hardcoded string is fine for submission.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-production-key")
app.config["DATABASE"] = "student_tracker.db"

tracker = StudentTracker(app.config["DATABASE"])

@app.route("/")
def dashboard():
    students = [s.as_dict() for s in tracker.list_students()]
    return render_template("dashboard.html", students=students)

@app.route("/students/new", methods=["GET", "POST"])
def new_student():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "")
        name = request.form.get("name", "")
        
        ok, message = tracker.enroll_student(roll_no, name)
        
        flash(message, "success" if ok else "danger")
        if ok:
            return redirect(url_for("dashboard"))

    return render_template("new_student.html")

@app.route("/scores/new", methods=["GET", "POST"])
def new_score():
    students = [s.as_dict() for s in tracker.list_students()]

    if request.method == "POST":
        try:
            value = int(request.form.get("value", ""))
        except ValueError:
            flash("Score must be a whole number.", "danger")
            return render_template("new_score.html", students=students)

        ok, message = tracker.record_score(
            request.form.get("roll_no", ""), request.form.get("subject", ""), value
        )
        flash(message, "success" if ok else "danger")
        if ok:
            return redirect(url_for("dashboard"))

    return render_template("new_score.html", students=students)

@app.route("/students/<roll_no>")
def student_profile(roll_no):
    student = tracker.get_student(roll_no)
    if not student:
        flash(f"No student found with roll number {roll_no}.", "warning")
        return redirect(url_for("dashboard"))

    return render_template("student_profile.html", student=student.as_dict())

@app.route("/students/<roll_no>/delete", methods=["POST"])
def delete_student(roll_no):
    ok, message = tracker.remove_student(roll_no)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("dashboard"))

@app.route("/insights", methods=["GET", "POST"])
def insights():
    subjects = tracker.list_subjects()
    result, selected = None, None

    if request.method == "POST":
        selected = request.form.get("subject", "").strip()

        if not selected:
            flash("Choose a subject first.", "warning")
        else:
            top = tracker.subject_topper(selected)
            if not top:
                flash(f"No scores recorded yet for {selected}.", "warning")
            else:
                name, roll_no, score = top
                result = {
                    "subject": selected,
                    "top_name": name,
                    "top_roll_no": roll_no,
                    "top_score": score,
                    "class_average": tracker.subject_average(selected),
                }

    return render_template("insights.html", subjects=subjects, result=result, selected=selected)

@app.route("/export")
def export_backup():
    filename, csv_text = tracker.export_csv()
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

if __name__ == "__main__":
    app.run(debug=True)