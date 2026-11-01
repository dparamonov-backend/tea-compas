from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "bookings.db"

app = Flask(__name__)
app.secret_key = "change-this-secret-before-deployment"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                ceremony TEXT NOT NULL,
                guests TEXT NOT NULL,
                preferred_date TEXT NOT NULL,
                comment TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/booking", methods=["POST"])
def booking():
    name = request.form.get("name", "").strip()
    contact = request.form.get("contact", "").strip()
    ceremony = request.form.get("ceremony", "").strip()
    guests = request.form.get("guests", "").strip()
    preferred_date = request.form.get("preferred_date", "").strip()
    comment = request.form.get("comment", "").strip()

    if not all([name, contact, ceremony, guests, preferred_date]):
        flash("Заполните, пожалуйста, все обязательные поля.", "error")
        return redirect(url_for("index") + "#booking")

    with get_db() as db:
        db.execute(
            """INSERT INTO bookings
               (name, contact, ceremony, guests, preferred_date, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, contact, ceremony, guests, preferred_date, comment,
             datetime.now().isoformat(timespec="seconds"))
        )

    flash("Заявка сохранена. Для подтверждения времени свяжитесь с чайным мастером.", "success")
    return redirect(url_for("index") + "#booking")


@app.route("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(debug=True)
