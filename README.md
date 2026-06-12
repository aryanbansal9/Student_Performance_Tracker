# Student Performance Tracker

A web application for teachers to track student performance across subjects — built with Python, Flask, and SQLite.

**Live demo:** _add your deployed URL here after deployment_

---

## Features

- **Add students** with a unique roll number and name
- **Add grades** for any subject (0-100), with automatic average calculation
- **Dashboard** showing every student, their subjects, and overall average — colour-coded by performance
- **Student detail page** with a full subject-by-subject breakdown and letter grades (A-F)
- **Delete students** (removes their grades too)
- **Insights page** (bonus): find the subject topper and class average for any subject
- Server-side validation for every input (empty fields, out-of-range scores, duplicate roll numbers, non-numeric input)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLite |
| Frontend | HTML, CSS (Jinja2 templates) |
| Deployment | Gunicorn + Render / Heroku |

---

## Project Structure

```
student_tracker/
├── app.py              # Flask routes — connects web requests to database functions
├── models.py            # Student & StudentTracker classes (OOP core)
├── database.py           # All SQLite queries live here
├── requirements.txt      # Python dependencies
├── Procfile               # Tells the host how to start the app
├── templates/             # HTML pages (Jinja2)
│   ├── base.html          # Shared layout (navbar, flash messages)
│   ├── index.html         # Dashboard
│   ├── add_student.html
│   ├── add_grade.html
│   ├── student_detail.html
│   └── insights.html
└── static/
    └── style.css          # All styling
```

---

## How It Works (Architecture)

```
Browser  <-->  Flask (app.py)  <-->  database.py  <-->  SQLite (.db file)
                     |
                     v
              models.py (Student, StudentTracker classes)
```

- **`app.py`** is intentionally thin. It reads form data, calls a `database.py` function, and renders a template.
- **`database.py`** is the *only* file that talks to SQLite directly. If we ever switched to another database, only this file would change.
- **`models.py`** defines what a "Student" looks like in Python (independent of how it's stored).

### Database Schema

Two tables, linked by `roll_number`:

```
students                      grades
┌─────────────┬──────┐        ┌────┬─────────────┬─────────┬───────┐
│ roll_number │ name │        │ id │ roll_number │ subject │ score │
│ (PRIMARY)   │      │  <───  │    │ (FOREIGN)   │         │       │
└─────────────┴──────┘        └────┴─────────────┴─────────┴───────┘
```

- `ON DELETE CASCADE`: deleting a student automatically deletes their grades
- `UNIQUE (roll_number, subject)`: a student can only have one score per subject — adding the same subject again **updates** the existing score

---

## Running Locally

### 1. Install Python 3.10+

Check with:
```bash
python3 --version
```

### 2. Clone or download this project

### 3. (Recommended) Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the app

```bash
python3 app.py
```

### 6. Open your browser

Go to: **http://127.0.0.1:5000**

The database file (`student_tracker.db`) is created automatically on first run.

---

## Using the App

1. **Add a student** — go to "Add Student", enter a roll number and name
2. **Add grades** — go to "Add Grade", select the student, type a subject (e.g. "Math") and score (0-100)
   - Use **consistent spelling** for subjects (e.g. always "Math", not sometimes "math") — this matters for the Insights page
3. **View the dashboard** — every student is listed with their average, colour-coded:
   - 🟢 Green: average ≥ 75
   - 🟡 Yellow: average 50-74
   - 🔴 Red: average < 50
4. **Click "View"** on any student for a detailed subject breakdown with letter grades
5. **Go to "Insights"** — pick a subject to see who scored the highest and the class average

---

## Edge Cases Handled

| Scenario | Behaviour |
|---|---|
| Duplicate roll number | Rejected with a clear error message |
| Empty name / roll number | Rejected before reaching the database |
| Score outside 0-100 | Rejected, both in the browser and on the server |
| Non-numeric score (e.g. "abc") | Caught with a friendly error, no crash |
| Adding the same subject twice for one student | The score is **updated**, not duplicated |
| Viewing/deleting a roll number that doesn't exist | Friendly error message, no crash |
| No students yet | Dashboard shows a helpful "Add your first student" prompt |
| No grades yet for Insights | Insights page tells you to add grades first |

---

## Deployment

This app is ready to deploy to **Render** or **Heroku** using the included `Procfile` and `requirements.txt`.

> **Note on the database:** SQLite stores data in a single file (`student_tracker.db`). On most free hosting tiers, the filesystem resets on every redeploy/restart — meaning your data won't persist long-term in production. This is fine for a demo/portfolio project. For a real production app, you'd swap SQLite for a hosted database (e.g. PostgreSQL) — and because all our database code lives in `database.py`, that change wouldn't touch `app.py` or `models.py` at all.

See the deployment guide for step-by-step instructions.

---

## Possible Future Improvements

- User authentication (so each teacher only sees their own students)
- Export class results to CSV/PDF
- Edit existing grades from the dashboard (currently you re-add to update)
- Charts/graphs for visual performance trends over time
- Switch to PostgreSQL for persistent production storage

---

## Author

Built as part of a Python internship project to practice OOP, SQLite, Flask, and web deployment.
