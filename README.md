# Gradebook – Student Performance Tracker

This is my mini project for my Python internship. It's a web app where
teachers can track their students' scores across different subjects. Built
it using Flask and SQLite, which I was learning alongside building this so
some parts took a while to figure out.

# Live Demo: https://student-performance-tracker-zz8o.onrender.com

## What it does

- Enroll students (name + roll number)
- Record a score for any subject. If you add the same subject again for
  the same student it updates the score instead of making a duplicate
- Dashboard shows all students with their overall average, colour coded
  so you can see at a glance who's doing well
- Click on a student to see their scores subject by subject with letter
  grades (A to F)
- Insights page where you can pick a subject and see who scored the
  highest and what the class average is
- Export as CSV – downloads the full data as a spreadsheet backup
- Remove a student and their scores get deleted too

## How to run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

First time you run it, it creates a `student_tracker.db` file automatically.
That's where all the data is stored.

## Project structure

```
STUDENT_TRACKER_PROJECT/
├── app.py               # Flask routes and application logic
├── database.py          # StudentTracker class (all SQLite queries)
├── models.py            # Student class (data models)
├── static/
│   └── style.css        # Custom styling
├── templates/           # HTML files (Jinja2)
│   ├── base.html
│   ├── dashboard.html
│   ├── insights.html
│   ├── new_score.html
│   ├── new_student.html
│   └── student_profile.html
├── Procfile             # Deployment commands
└── requirements.txt     # Python dependencies
```

I tried to keep `app.py` clean and just handle the web stuff, while
`database.py` does all the actual database work. Probably not perfect
but it made things easier to debug.

## Tech used

- Python + Flask
- SQLite (via the built-in sqlite3 module, no ORM)
- Jinja2 for the HTML templates
- Custom CSS for styling

## Things I had to handle

A few things that could go wrong that I made sure to deal with:

- someone entering the same roll number twice → shows an error
- leaving name or roll number blank → rejects it
- entering a score like 150 or -5 → rejects it
- typing letters into the score field → doesn't crash, shows a message
- going to a URL for a student that doesn't exist → redirects cleanly
- the insights page when there's no data yet → shows a message instead
  of breaking

## Deployment

Has a `Procfile` so it should work on Render or Heroku.
Start command is `gunicorn app:app`.

One thing to note – SQLite saves the database as a file on the server.
On Render's free tier that file resets whenever the app restarts, so
data doesn't persist long term. Fine for a demo but would need Postgres
or something similar for actual use.

## What I'd change if I kept working on it

- Subject names are case sensitive right now so "math" and "Math" get
  treated as different. Would fix this by lowercasing before saving
- No authentication, any user can see and edit everything
- Would be nice to have some charts for visualizing scores over time
- Haven't tested with a large number of students so not sure how it
  performs at scale

---

*Aryan Bansal – Python Internship Project*
