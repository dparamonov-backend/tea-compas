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

TELEGRAM_URL = "https://t.me/tea_compas"

# Existing ceremonies (their pages are in static/images/menu) — used in the booking form.
BASE_CEREMONIES = [
    "Знакомство с пуэрами", "Изумрудный путь", "Искусство улунов",
    "Золото китайского красного чая", "Чайная экзотика", "Ароматы чёрного чая",
    "Мир ройбоса", "Шесть сокровищ Поднебесной", "Изящный мир белых и жёлтых чаёв",
]

# New ceremonies shown as cards with a detail window. Prices are examples — edit freely.
NEW_CEREMONIES = [
    {
        "id": "matcha", "art": "matcha", "title": "Матча-церемония",
        "tagline": "Японский ритуал яркого зелёного порошка",
        "price": "5 400 ₽", "per": "/ 2 участника", "duration": "90 минут", "guests": "2–6 гостей",
        "quote": "Матча — это пауза, в которой слышно, как шумит вода.",
        "teas": [
            ["Матча Удзи", "Нежная, сладковатая, с морской свежестью."],
            ["Хойтидзя матча", "Плотная пена и глубокий травяной вкус."],
            ["Гёкуро", "Тенистый чай с умами-послевкусием."],
            ["Матча-латте", "Мягкий финал с молоком по желанию."],
        ],
        "learn": ["Откуда пришла матча и чем она отличается от обычного чая", "Как выбрать чашу и бамбуковый венчик",
                  "Как взбить пену без комочков", "Японские сладости вагаси и их пары"],
        "flow": ["Приветствие и знакомство с посудой", "Мастер взбивает первую чашу", "Вы пробуете сами под подсказки",
                 "Дегустация четырёх вкусов", "Разговор и вопросы"],
    },
    {
        "id": "sakura", "art": "sakura", "title": "Цветочная церемония «Сакура»",
        "tagline": "Весенний вечер из цветов, нектара и лёгкого чая",
        "price": "5 200 ₽", "per": "/ 2 участника", "duration": "75 минут", "guests": "2–5 гостей",
        "quote": "Самое красивое в цветочном чае — как он раскрывается.",
        "teas": [
            ["Жасминовые жемчужины", "Свёрнутые бутоны раскрываются в чайнике."],
            ["Сакура-сенча", "Зелёный чай с лепестками цветущей сакуры."],
            ["Хризантема с мёдом", "Прозрачный золотой настой, мягкий вкус."],
            ["Османтусовый улун", "Абрикосовый аромат и долгое послевкусие."],
        ],
        "learn": ["Как цветочные чаи делают в Китае и Японии", "Почему цветы не заваривают кипятком",
                  "Как «читать» аромат в тёплой чашке", "Какие сладости подчёркивают цветочные ноты"],
        "flow": ["Встреча и выбор стеклянного чайника", "Раскрытие бутонов на ваших глазах",
                 "Дегустация четырёх цветочных чаёв", "Лёгкая закуска к чаю", "Беседа и фото на память"],
    },
    {
        "id": "duo", "art": "duo", "title": "Чай на двоих",
        "tagline": "Спокойный вечер для пары: чай, тишина, разговор",
        "price": "6 200 ₽", "per": "/ 2 участника", "duration": "2 часа", "guests": "для двоих",
        "quote": "Хороший чай не нужно объяснять — его достаточно разделить.",
        "teas": [
            ["Те Гуань Инь", "Светлый улун с цветочным ароматом."],
            ["Дянь Хун", "Красный чай с мёдом и какао в послевкусии."],
            ["Бай Му Дань", "Белый чай, тонкий и солнечный."],
            ["Шу пуэр", "Тёплый, землистый, оставляет тепло."],
        ],
        "learn": ["Как заваривать чай по-китайски вдвоём", "Как менять вкус от пролива к проливу",
                  "Что подарить любителю чая", "Как выбрать чай домой"],
        "flow": ["Отдельный стол и приглушённый свет", "Мастер ведёт первые проливы", "Вы завариваете сами",
                 "Мини-сет сладостей в подарок к чаю", "Свободное общение без спешки"],
    },
    {
        "id": "dessert", "art": "dessert", "title": "Чай и десерты",
        "tagline": "Гастрономическая пара: каждому десерту свой чай",
        "price": "5 900 ₽", "per": "/ 2 участника", "duration": "90 минут", "guests": "2–6 гостей",
        "quote": "Хороший десерт делает чай ярче, а чай — десерт тоньше.",
        "teas": [
            ["Дянь Хун и тарталетки", "Малиновая кислинка рядом с мёдом."],
            ["Тайваньский улун и «Наполеон»", "Сливочные слои и цветочная лёгкость."],
            ["Ягодный пуэр и корзинка с голубикой", "Тёмная ягода к тёмному чаю."],
            ["Белый чай и сырная тарелка", "Нежное сочетание с мягкими сырами."],
        ],
        "learn": ["Как строить чайные пары по вкусу", "Почему сладкое меняет чай",
                  "Как сочетать чай и сыр", "Как подавать чай гостям дома"],
        "flow": ["Знакомство и ароматы", "Первая пара: чай и десерт", "Вторая и третья пары",
                 "Сырная пара для контраста", "Обсуждение любимого сочетания"],
    },
    {
        "id": "team", "art": "team", "title": "Чайная встреча для компании",
        "tagline": "Командный ритуал для друзей, коллег и больших семей",
        "price": "от 2 400 ₽", "per": "/ человек", "duration": "2 часа", "guests": "6–12 гостей",
        "quote": "Один чайник — и вся компания за одним столом.",
        "teas": [
            ["Дегустационный круг", "Пять чаёв по одному на каждый стиль."],
            ["Чайный квиз", "Угадайте чай по аромату и цвету."],
            ["Коллективный пролив", "Каждый заваривает свою чашу."],
            ["Сет закусок", "Лёгкая еда из нашего меню блюд."],
        ],
        "learn": ["Как провести чаепитие на большую группу", "Что сплачивает лучше разговора",
                  "Как выбрать чай для подарка коллегам", "Чайные традиции разных стран"],
        "flow": ["Встреча и рассадка за общим столом", "Короткая история чая", "Чайный квиз и дегустация",
                 "Свободное общение и закуски", "Выбор и покупка чая с собой"],
    },
]


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
    menu_pages = [f"images/menu/page-{n:02d}.webp" for n in range(1, 10)] + ["images/food-menu.webp"]
    return render_template(
        "index.html",
        telegram_url=TELEGRAM_URL,
        base_ceremonies=BASE_CEREMONIES,
        new_ceremonies=NEW_CEREMONIES,
        menu_pages=menu_pages,
    )


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
