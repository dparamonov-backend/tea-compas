from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "bookings.db"
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-before-deployment")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "").strip()


def send_telegram_notification(text):
    """Send a booking notification to the admin, if Telegram is configured."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_ID:
        return False, "Telegram не настроен: добавьте токен и ID администратора в .env."

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_ADMIN_ID,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
        if result.get("ok"):
            return True, None
        return False, result.get("description", "Telegram API вернул ошибку.")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, str(exc)


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

    notification = (
        "🍵 Новая заявка на чайную церемонию\\n\\n"
        f"Имя: {name}\\n"
        f"Контакт: {contact}\\n"
        f"Церемония: {ceremony}\\n"
        f"Количество гостей: {guests}\\n"
        f"Желаемая дата: {preferred_date}\\n"
        f"Комментарий: {comment or 'не указан'}\\n\\n"
        "Заявка сохранена в базе сайта. Бронирование ещё не подтверждено."
    )
    sent, send_error = send_telegram_notification(notification)
    if sent:
        flash("Заявка сохранена и отправлена администратору в Telegram. Бронирование будет подтверждено отдельно.", "success")
    else:
        app.logger.warning("Telegram booking notification failed: %s", send_error)
        flash("Заявка сохранена в базе сайта, но уведомление в Telegram не отправилось. Проверьте настройки бота.", "error")
    return redirect(url_for("index") + "#booking")


@app.route("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(debug=True)
