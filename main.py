# =============================================================================
#  TONgueNG — приложение для изучения иностранных слов
#  Python + Flet 1.x + PostgreSQL, весь код (интерфейс и база) в одном файле
#  Запуск: python main.py
# =============================================================================

import hashlib
import random
import re
import secrets
from datetime import date

import flet as ft
import psycopg2

# -----------------------------------------------------------------------------
#  1. НАСТРОЙКИ — при необходимости измените под себя
# -----------------------------------------------------------------------------
DB_HOST = "ep-autumn-lake-ba3tm4kh.c-8.eu-central-1.aws.neon.tech"
DB_PORT = 5432
DB_USER = "neondb_owner"
DB_PASSWORD = "npg_RhTYobDiHs76"     # <-- укажите свой пароль PostgreSQL
DB_NAME = "tongue_ng"

XP_PER_LEVEL = 100           # сколько XP нужно на новый уровень
MAX_QUESTIONS = 10           # сколько слов в одной тренировке

# цвета интерфейса
BG = "#101426"
CARD = "#1B2140"
ACCENT = "#7C5CFF"
TEXT = "#F2F4FF"
MUTED = "#98A0C4"
GREEN = "#2BD9A8"
RED = "#FF5C7A"
AMBER = "#FFB547"

MODES = {
    "cards": "Карточки",
    "choice": "Выбор перевода",
    "typing": "Ввод перевода",
}

# поддерживаемые языки: код -> название
LANGUAGES = {
    "en": "Английский",
    "ru": "Русский",
    "zh": "Китайский",
    "ja": "Японский",
    "ar": "Арабский",
    "es": "Испанский",
    "fr": "Французский",
    "de": "Немецкий",
    "kk": "Казахский",
    "hi": "Хинди",
    "ko": "Корейский",
}

# слова, которые получает каждый новый пользователь:
# код языка -> [(слово, перевод), ...]
# у всех языков перевод русский, у русского — английский
START_WORDS = {
    "en": [
        ("apple", "яблоко"), ("house", "дом"), ("water", "вода"),
        ("book", "книга"), ("friend", "друг"), ("morning", "утро"),
        ("window", "окно"), ("road", "дорога"), ("dream", "мечта"),
        ("letter", "письмо"), ("music", "музыка"), ("weather", "погода"),
        ("sun", "солнце"), ("rain", "дождь"), ("city", "город"),
        ("ticket", "билет"), ("hotel", "отель"), ("map", "карта"),
        ("meeting", "встреча"), ("report", "отчёт"),
    ],
    "ru": [
        ("яблоко", "apple"), ("дом", "house"), ("вода", "water"),
        ("книга", "book"), ("друг", "friend"), ("утро", "morning"),
        ("окно", "window"), ("дорога", "road"), ("мечта", "dream"),
        ("письмо", "letter"), ("музыка", "music"), ("погода", "weather"),
        ("солнце", "sun"), ("дождь", "rain"), ("город", "city"),
    ],
    "zh": [
        ("苹果", "яблоко"), ("房子", "дом"), ("水", "вода"),
        ("书", "книга"), ("朋友", "друг"), ("早上", "утро"),
        ("窗户", "окно"), ("路", "дорога"), ("梦想", "мечта"),
        ("信", "письмо"), ("音乐", "music"), ("天气", "погода"),
        ("太阳", "солнце"), ("雨", "дождь"), ("城市", "город"),
    ],
    "ja": [
        ("りんご", "яблоко"), ("家", "дом"), ("水", "вода"),
        ("本", "книга"), ("友達", "друг"), ("朝", "утро"),
        ("窓", "окно"), ("道", "дорога"), ("夢", "мечта"),
        ("手紙", "письмо"), ("音楽", "музыка"), ("天気", "погода"),
        ("太陽", "солнце"), ("雨", "дождь"), ("都市", "город"),
    ],
    "ar": [
        ("تفاحة", "яблоко"), ("بيت", "дом"), ("ماء", "вода"),
        ("كتاب", "книга"), ("صديق", "друг"), ("صباح", "утро"),
        ("نافذة", "окно"), ("طريق", "дорога"), ("حلم", "мечта"),
        ("رسالة", "письмо"), ("موسيقى", "музыка"), ("طقس", "погода"),
        ("شمس", "солнце"), ("مطر", "дождь"), ("مدينة", "город"),
    ],
    "es": [
        ("manzana", "яблоко"), ("casa", "дом"), ("agua", "вода"),
        ("libro", "книга"), ("amigo", "друг"), ("mañana", "утро"),
        ("ventana", "окно"), ("camino", "дорога"), ("sueño", "мечта"),
        ("carta", "письмо"), ("música", "музыка"), ("tiempo", "погода"),
        ("sol", "солнце"), ("lluvia", "дождь"), ("ciudad", "город"),
    ],
    "fr": [
        ("pomme", "яблоко"), ("maison", "дом"), ("eau", "вода"),
        ("livre", "книга"), ("ami", "друг"), ("matin", "утро"),
        ("fenêtre", "окно"), ("route", "дорога"), ("rêve", "мечта"),
        ("lettre", "письмо"), ("musique", "музыка"), ("temps", "погода"),
        ("soleil", "солнце"), ("pluie", "дождь"), ("ville", "город"),
    ],
    "de": [
        ("Apfel", "яблоко"), ("Haus", "дом"), ("Wasser", "вода"),
        ("Buch", "книга"), ("Freund", "друг"), ("Morgen", "утро"),
        ("Fenster", "окно"), ("Straße", "дорога"), ("Traum", "мечта"),
        ("Brief", "письмо"), ("Musik", "музыка"), ("Wetter", "погода"),
        ("Sonne", "солнце"), ("Regen", "дождь"), ("Stadt", "город"),
    ],
    "kk": [
        ("алма", "яблоко"), ("үй", "дом"), ("су", "вода"),
        ("кітап", "книга"), ("дос", "друг"), ("таң", "утро"),
        ("терезе", "окно"), ("жол", "дорога"), ("арман", "мечта"),
        ("хат", "письмо"), ("музыка", "музыка"), ("ауа райы", "погода"),
        ("күн", "солнце"), ("жаңбыр", "дождь"), ("қала", "город"),
    ],
    "hi": [
        ("सेब", "яблоко"), ("घर", "дом"), ("पानी", "вода"),
        ("किताब", "книга"), ("दोस्त", "друг"), ("सुबह", "утро"),
        ("खिड़की", "окно"), ("सड़क", "дорога"), ("सपना", "мечта"),
        ("पत्र", "письмо"), ("संगीत", "музыка"), ("मौसम", "погода"),
        ("सूरज", "солнце"), ("बारिश", "дождь"), ("शहर", "город"),
    ],
    "ko": [
        ("사과", "яблоко"), ("집", "дом"), ("물", "вода"),
        ("책", "книга"), ("친구", "друг"), ("아침", "утро"),
        ("창문", "окно"), ("길", "дорога"), ("꿈", "мечта"),
        ("편지", "письмо"), ("음악", "музыка"), ("날씨", "погода"),
        ("태양", "солнце"), ("비", "дождь"), ("도시", "город"),
    ],
}

# схема базы данных: создаётся автоматически при запуске
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(24) NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    xp            INTEGER     NOT NULL DEFAULT 0,
    lang          VARCHAR(8)  NOT NULL DEFAULT 'en',
    created_at    TIMESTAMP   NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS words (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word          VARCHAR(100) NOT NULL,
    translation   VARCHAR(150) NOT NULL,
    lang          VARCHAR(8)   NOT NULL DEFAULT 'en',
    correct_count INTEGER      NOT NULL DEFAULT 0,
    wrong_count   INTEGER      NOT NULL DEFAULT 0,
    learned       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS results (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mode       VARCHAR(30) NOT NULL,
    total      INTEGER     NOT NULL,
    correct    INTEGER     NOT NULL,
    xp         INTEGER     NOT NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS lang VARCHAR(8) NOT NULL DEFAULT 'en';
ALTER TABLE words ADD COLUMN IF NOT EXISTS lang VARCHAR(8) NOT NULL DEFAULT 'en';

-- старое ограничение «одно слово на пользователя» заменяем на «одно слово на язык»
ALTER TABLE words DROP CONSTRAINT IF EXISTS words_user_id_word_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_words_user_lang_word
    ON words(user_id, lang, lower(word));

CREATE INDEX IF NOT EXISTS idx_words_user   ON words(user_id);
CREATE INDEX IF NOT EXISTS idx_words_lang   ON words(user_id, lang);
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
"""

# состояние приложения (окно одно — пользователь один)
STATE = {
    "user": None,        # {"id", "username", "xp", "lang"}
    "search": "",        # строка поиска в словаре
    "mode": "",          # текущий режим тренировки
    "questions": [],     # вопросы тренировки
    "index": 0,          # номер текущего вопроса
    "correct": 0,        # верных ответов в тренировке
    "feedback": None,    # результат последнего ответа
    "result": None,      # итог завершённой тренировки
    "flipped": False,    # переворот карточки
}


# =============================================================================
#  2. БАЗА ДАННЫХ
# =============================================================================
def connect_to_db(dbname=None):
    """Подключение к PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=dbname or DB_NAME,
        sslmode="require",
        connect_timeout=5,
    )


def execute_query(sql, params=(), fetch=False):
    """Выполняет SQL-запрос и фиксирует изменения.

    fetch=True  -> возвращает список строк в виде словарей (для SELECT);
    fetch=False -> возвращает число затронутых строк.
    """
    conn = connect_to_db()
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            if fetch:
                columns = [col[0] for col in cur.description]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            else:
                rows = cur.rowcount
            conn.commit()
            return rows
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


def setup_database():
    """Создаёт базу данных (если её нет) и все таблицы."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname="postgres",
        connect_timeout=5,
    )
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        cur.close()
    finally:
        conn.close()
    execute_query(SCHEMA)      # создаём таблицы и индексы


# =============================================================================
#  3. ПАРОЛИ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================
def hash_password(password):
    """Превращает пароль в хеш PBKDF2 (в базе пароля нет)."""
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return salt + "$" + digest.hex()


def check_password(password, stored):
    """Сверяет введённый пароль с сохранённым хешем."""
    try:
        salt, digest = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
        return check.hex() == digest
    except (ValueError, AttributeError):
        return False


def normalize(text):
    """Приводит ответ к одному виду: регистр, пробелы, знаки препинания."""
    text = str(text or "").strip().lower()
    text = re.sub(r"[.,!?;:\"'«»()]", "", text)
    return re.sub(r"\s+", " ", text)


def level_of(xp):
    """Уровень по опыту: каждые 100 XP — новый уровень."""
    return xp // XP_PER_LEVEL + 1


def mask_word(word):
    """Делает подсказку для оборота карточки: 'apple' -> 'a _ _ _ e (5 букв)'."""
    w = str(word).strip()
    if len(w) <= 2:
        return f"{w[0]} _ ({len(w)} букв)"
    middle = " ".join("_" for _ in w[1:-1])
    return f"{w[0]} {middle} {w[-1]} ({len(w)} букв)"


# =============================================================================
#  4. ПОЛЬЗОВАТЕЛИ
# =============================================================================
def add_start_words(user_id):
    """Добавляет стартовые слова по всем языкам (пропускает уже существующие)."""
    for lang, pairs in START_WORDS.items():
        for word, translation in pairs:
            execute_query(
                "INSERT INTO words (user_id, word, translation, lang) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (user_id, word, translation, lang),
            )


def register_user(username, password):
    """Регистрация: создаёт аккаунт и добавляет стартовые слова."""
    username = (username or "").strip()
    password = password or ""
    if len(username) < 3:
        raise ValueError("Логин должен содержать минимум 3 символа")
    if len(password) < 6:
        raise ValueError("Пароль должен содержать минимум 6 символов")
    if username.lower() == "guest":
        raise ValueError("Этот логин зарезервирован для гостевого входа")
    if execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch=True):
        raise ValueError("Такой логин уже занят")

    rows = execute_query(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) "
        "RETURNING id, username, xp, lang",
        (username, hash_password(password)),
        fetch=True,
    )
    user = rows[0]
    add_start_words(user["id"])
    return user


def login_user(username, password):
    """Вход: проверяет логин и пароль."""
    rows = execute_query(
        "SELECT id, username, xp, lang, password_hash FROM users WHERE username = %s",
        ((username or "").strip(),),
        fetch=True,
    )
    if not rows or not check_password(password or "", rows[0]["password_hash"]):
        raise ValueError("Неверный логин или пароль")
    user = rows[0]
    user.pop("password_hash")
    return user


def guest_user():
    """Гостевой аккаунт: работа без регистрации, данные сохраняются в базе."""
    rows = execute_query(
        "SELECT id, username, xp, lang FROM users WHERE username = 'guest'",
        fetch=True,
    )
    if rows:
        add_start_words(rows[0]["id"])
        return rows[0]

    rows = execute_query(
        "INSERT INTO users (username, password_hash) VALUES ('guest', %s) "
        "RETURNING id, username, xp, lang",
        (hash_password(secrets.token_hex(16)),),
        fetch=True,
    )
    user = rows[0]
    add_start_words(user["id"])
    return user


def add_xp(user_id, amount):
    """Начисляет опыт и возвращает новое значение."""
    rows = execute_query(
        "UPDATE users SET xp = xp + %s WHERE id = %s RETURNING xp",
        (amount, user_id),
        fetch=True,
    )
    return rows[0]["xp"] if rows else 0


def set_language(user_id, lang):
    """Запоминает язык обучения: он хранится в базе и переживает перезапуск."""
    if lang not in LANGUAGES:
        raise ValueError("Неизвестный язык")
    execute_query("UPDATE users SET lang = %s WHERE id = %s", (lang, user_id))
    if STATE["user"]:
        STATE["user"]["lang"] = lang


# =============================================================================
#  5. СЛОВАРЬ
# =============================================================================
def add_word(user_id, word, translation, lang="en"):
    """Добавляет слово в словарь пользователя на выбранном языке."""
    word = (word or "").strip()
    translation = (translation or "").strip()
    if lang not in LANGUAGES:
        raise ValueError("Неизвестный язык")
    if not word or not translation:
        raise ValueError("Заполните слово и перевод")
    if execute_query(
        "SELECT id FROM words WHERE user_id = %s AND lang = %s "
        "AND lower(word) = lower(%s)",
        (user_id, lang, word),
        fetch=True,
    ):
        raise ValueError("Такое слово уже есть в словаре")
    execute_query(
        "INSERT INTO words (user_id, word, translation, lang) "
        "VALUES (%s, %s, %s, %s)",
        (user_id, word, translation, lang),
    )


def get_words(user_id, lang=None, search=""):
    """Слова пользователя: при lang — только выбранный язык, с поиском."""
    search = (search or "").strip()
    sql = "SELECT * FROM words WHERE user_id = %s"
    params = [user_id]
    if lang:
        sql += " AND lang = %s"
        params.append(lang)
    if search:
        pattern = f"%{search}%"
        sql += " AND (word ILIKE %s OR translation ILIKE %s)"
        params += [pattern, pattern]
    sql += " ORDER BY id DESC"
    return execute_query(sql, tuple(params), fetch=True)


def delete_word(word_id, user_id):
    """Удаляет слово пользователя."""
    execute_query("DELETE FROM words WHERE id = %s AND user_id = %s", (word_id, user_id))


def update_word_progress(word_id, is_right):
    """Обновляет счётчики ответов. Три верных ответа — слово выучено."""
    if is_right:
        execute_query(
            "UPDATE words SET correct_count = correct_count + 1, "
            "learned = (correct_count + 1 >= 3) WHERE id = %s",
            (word_id,),
        )
    else:
        execute_query(
            "UPDATE words SET wrong_count = wrong_count + 1, learned = FALSE WHERE id = %s",
            (word_id,),
        )


# =============================================================================
#  6. ТРЕНИРОВКА И СТАТИСТИКА
# =============================================================================
def build_questions(user_id, mode, lang=None):
    """Готовит вопросы для выбранного режима и языка с гарантированным перемешиванием."""
    words = list(get_words(user_id, lang))
    if not words:
        raise ValueError("На этом языке пока нет слов — добавьте их в словарь")

    rng = random.SystemRandom()
    rng.shuffle(words)
    pool = words[:MAX_QUESTIONS]
    rng.shuffle(pool)

    questions = []
    for word in pool:
        if mode == "cards":
            # В карточках показываем перевод, пользователь сам вводит иностранное слово
            question = {
                "word_id": word["id"],
                "prompt": word["translation"],
                "answer": word["word"],
                "options": [],
            }
        else:
            question = {
                "word_id": word["id"],
                "prompt": word["word"],
                "answer": word["translation"],
                "options": [],
            }
            if mode == "choice":
                others = [
                    w["translation"] for w in words
                    if w["id"] != word["id"] and w["translation"] != word["translation"]
                ]
                question["options"] = [word["translation"]] + rng.sample(
                    others, min(3, len(others))
                )
                rng.shuffle(question["options"])
        questions.append(question)
    return questions


def save_result(user_id, mode, total, correct, xp):
    """Сохраняет итог тренировки в таблицу results."""
    execute_query(
        "INSERT INTO results (user_id, mode, total, correct, xp) VALUES (%s, %s, %s, %s, %s)",
        (user_id, mode, total, correct, xp),
    )


def get_results(user_id, limit=10):
    """Последние тренировки пользователя."""
    return execute_query(
        "SELECT * FROM results WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit),
        fetch=True,
    )


def get_stats(user_id, lang=None):
    """Сводная статистика по словарю (всего или по одному языку)."""
    sql = (
        "SELECT COUNT(*) AS total, "
        "COUNT(*) FILTER (WHERE learned) AS learned, "
        "COALESCE(SUM(correct_count), 0) AS correct, "
        "COALESCE(SUM(wrong_count), 0) AS wrong "
        "FROM words WHERE user_id = %s"
    )
    params = [user_id]
    if lang:
        sql += " AND lang = %s"
        params.append(lang)
    rows = execute_query(sql, tuple(params), fetch=True)
    stats = rows[0] if rows else {"total": 0, "learned": 0, "correct": 0, "wrong": 0}
    answers = stats["correct"] + stats["wrong"]
    stats["accuracy"] = round(100 * stats["correct"] / answers) if answers else 0
    return stats


# =============================================================================
#  7. МЕЛКИЕ ЭЛЕМЕНТЫ ИНТЕРФЕЙСА
# =============================================================================
def t(value, size=14, color=TEXT, weight=None, max_lines=None):
    """Короткий помощник для текста."""
    return ft.Text(
        str(value),
        size=size,
        color=color,
        weight=weight,
        max_lines=max_lines,
        overflow=ft.TextOverflow.ELLIPSIS if max_lines else None,
    )


def card(content, bgcolor=CARD, padding=14, on_click=None):
    """Плашка с закруглёнными углами."""
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=padding,
        border_radius=16,
        border=ft.Border.all(1, "#2A3157"),
        on_click=on_click,
        ink=bool(on_click),
    )


def snack(page, text, error=False):
    """Всплывающее сообщение внизу экрана."""
    page.show_dialog(ft.SnackBar(ft.Text(text, color=ft.Colors.WHITE),
                          bgcolor=RED if error else GREEN))
    
    
def field_border():
    """Единый стиль рамки для TextField по стандарту Flet 1.x."""
    return {
        ft.ControlState.DEFAULT: ft.OutlineInputBorder(
            border_radius=12,
            side=ft.BorderSide(1, "#2A3157"),
        ),
        ft.ControlState.FOCUSED: ft.OutlineInputBorder(
            border_radius=12,
            side=ft.BorderSide(2, ACCENT),
        ),
    }


def language_selector(page):
    """Выпадающий список языков: выбор сохраняется в базе."""
    def change(e):
        STATE["search"] = ""
        set_language(STATE["user"]["id"], e.control.value)
        go_to(page, STATE.get("tab", "home"))

    return ft.Dropdown(
        value=STATE["user"].get("lang", "en"),
        options=[
            ft.DropdownOption(
                key=code,
                text=name,
                style=ft.ButtonStyle(color=TEXT),
            )
            for code, name in LANGUAGES.items()
        ],
        on_select=change,
        filled=True,
        fill_color=CARD,
        menu_style=ft.MenuStyle(bgcolor=CARD),
        text_style=ft.TextStyle(color=TEXT, size=14, weight=ft.FontWeight.W_500),
        border={
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(1, "#2A3157"),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(2, ACCENT),
            ),
        },
        dense=True,
    )

# =============================================================================
#  8. ЭКРАН ВХОДА И РЕГИСТРАЦИИ
# =============================================================================
def show_auth(page):
    """Экран входа: логин, пароль, регистрация, гостевой режим."""
    login = ft.TextField(
        label="Логин", filled=True, bgcolor=CARD, border=field_border(),
        color=TEXT,
        on_submit=lambda e: submit(e),
    )
    password = ft.TextField(
        label="Пароль", password=True, can_reveal_password=True,
        filled=True, bgcolor=CARD, border=field_border(),
        color=TEXT,
        on_submit=lambda e: submit(e),
    )

    def submit(e, register=False):
        try:
            if register:
                user = register_user(login.value, password.value)
                snack(page, "Аккаунт создан, добавлены слова на всех языках")
            else:
                user = login_user(login.value, password.value)
        except ValueError as exc:
            snack(page, str(exc), error=True)
            return
        STATE.update(user=user, questions=[], feedback=None, result=None)
        go_to(page, "home")

    def guest(e):
        try:
            user = guest_user()
        except Exception as exc:
            snack(page, str(exc), error=True)
            return
        STATE.update(user=user, questions=[], feedback=None, result=None)
        go_to(page, "home")

    page.controls.clear()
    page.add(
        ft.Container(
            expand=True,
            padding=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),      # левый верхний угол
                end=ft.Alignment(1, 1),          # правый нижний угол
                colors=["#101426", "#1B1F44"],
            ),
            content=ft.Column(
                [
                    ft.Container(height=40),
                    ft.Icon(ft.Icons.TRANSLATE, size=54, color=ACCENT),
                    t("TONgueNG", 32, TEXT, ft.FontWeight.BOLD),
                    t("тренажёр иностранных слов", 12, MUTED),
                    ft.Container(height=18),
                    card(
                        ft.Column(
                            [
                                login,
                                password,
                                ft.Button(
                                    "Войти", on_click=submit, width=320, height=46,
                                    style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE),
                                ),
                                ft.OutlinedButton(
                                    "Регистрация",
                                    on_click=lambda e: submit(e, True),
                                    width=320, height=46,
                                    style=ft.ButtonStyle(color=ACCENT),
                                ),
                                ft.TextButton(
                                    "Продолжить без регистрации",
                                    on_click=guest,
                                    style=ft.ButtonStyle(color=GREEN),
                                ),
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=16,
                    ),
                    ft.Container(height=10),
                    t("Без входа используется гостевой аккаунт — прогресс сохраняется", 10, MUTED),
                ],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )
    page.update()


# =============================================================================
#  9. НАВИГАЦИЯ
# =============================================================================
def go_to(page, tab):
    """Показывает выбранный экран и нижнее меню."""
    STATE["tab"] = tab
    views = {
        "home": view_home,
        "dictionary": view_dictionary,
        "training": view_training,
        "stats": view_stats,
        "profile": view_profile,
    }
    nav = [
        ("home", "Главная", ft.Icons.HOME),
        ("dictionary", "Словарь", ft.Icons.MENU_BOOK),
        ("training", "Тренировка", ft.Icons.SCHOOL),
        ("stats", "Статистика", ft.Icons.INSIGHTS),
        ("profile", "Профиль", ft.Icons.PERSON),
    ]

    page.controls.clear()
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=views.get(tab, view_home)(page),
                    expand=True,
                    padding=ft.Padding.only(left=16, right=16, top=16, bottom=4),
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(
                                            icon, size=22,
                                            color=ACCENT if tab == key else MUTED,
                                        ),
                                        t(label, 10, ACCENT if tab == key else MUTED),
                                    ],
                                    spacing=2,
                                    tight=True,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                expand=True,
                                alignment=ft.Alignment(0, 0),    # по центру
                                padding=ft.Padding.symmetric(vertical=8),
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.12, ACCENT) if tab == key else None,
                                on_click=lambda e, k=key: go_to(page, k),
                                ink=True,
                            )
                            for key, label, icon in nav
                        ],
                        spacing=0,
                    ),
                    bgcolor=CARD,
                    border=ft.Border.only(top=ft.BorderSide(1, "#2A3157")),
                    padding=ft.Padding.only(left=8, right=8, bottom=4),
                ),
            ],
            spacing=0,
            expand=True,
        )
    )
    page.update()


# =============================================================================
#  10. ГЛАВНЫЙ ЭКРАН
# =============================================================================
def view_home(page):
    """Главная: язык, уровень, опыт, статистика, слово дня."""
    user = STATE["user"]
    lang = user.get("lang", "en")
    stats = get_stats(user["id"], lang)
    xp = user["xp"]
    level = level_of(xp)
    progress = (xp % XP_PER_LEVEL) / XP_PER_LEVEL

    def tile(label, value, color):
        return ft.Container(
            content=ft.Column(
                [t(value, 18, color, ft.FontWeight.BOLD), t(label, 10, MUTED, max_lines=2)],
                spacing=2,
                tight=True,
            ),
            expand=True,
            bgcolor=CARD,
            border_radius=14,
            padding=10,
            border=ft.Border.all(1, "#2A3157"),
        )

    words = get_words(user["id"], lang)
    if words:
        word = words[date.today().toordinal() % len(words)]
        word_block = card(
            ft.Column(
                [
                    t("Слово дня", 11, ACCENT, ft.FontWeight.W_600),
                    t(word["word"], 24, TEXT, ft.FontWeight.BOLD),
                    t(word["translation"], 14, MUTED),
                    t("выучено" if word["learned"] else "ещё учим", 10,
                      GREEN if word["learned"] else AMBER),
                ],
                spacing=4,
            )
        )
    else:
        word_block = card(
            t(f"На языке «{LANGUAGES.get(lang, lang)}» пока нет слов — "
              f"добавьте их в словаре", 12, MUTED)
        )

    name = "гость" if user["username"] == "guest" else user["username"]
    return ft.Column(
        [
            ft.Row(
                [
                    t(f"Привет, {name}!", 20, TEXT, ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    t(f"Уровень {level}", 12, ACCENT, ft.FontWeight.W_600),
                ]
            ),
            ft.Row(
                [
                    t("Язык", 11, MUTED),
                    ft.Container(content=language_selector(page), expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            card(
                ft.Column(
                    [
                        ft.Row([t(f"{xp} XP", 24, ACCENT, ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                t(f"до уровня {level + 1}", 10, MUTED)]),
                        ft.ProgressBar(value=progress, bar_height=8, color=ACCENT,
                                       bgcolor="#2A3157", border_radius=4),
                    ],
                    spacing=8,
                )
            ),
            ft.Row(
                [
                    tile("слов на языке", str(stats["total"]), TEXT),
                    tile("выучено", str(stats["learned"]), GREEN),
                    tile("точность", f"{stats['accuracy']}%", AMBER),
                ],
                spacing=8,
            ),
            word_block,
            ft.Button("Начать тренировку", height=48,
                              on_click=lambda e: go_to(page, "training"),
                              style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE)),
            ft.OutlinedButton("Добавить слово", height=44,
                              on_click=lambda e: open_word_dialog(page),
                              style=ft.ButtonStyle(color=ACCENT)),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


# =============================================================================
#  11. СЛОВАРЬ
# =============================================================================
def view_dictionary(page):
    """Словарь: язык, поиск, список слов, добавление, удаление."""
    user = STATE["user"]
    user_id = user["id"]
    lang = user.get("lang", "en")
    words_list = ft.Column(spacing=8)

    def fill_list():
        rows = get_words(user_id, lang, STATE.get("search", ""))
        if rows:
            words_list.controls = [word_row(word) for word in rows]
        else:
            words_list.controls = [t("Слова не найдены", 12, MUTED)]
        page.update()

    def remove(e, word_id):
        delete_word(word_id, user_id)
        fill_list()
        snack(page, "Слово удалено")

    def word_row(word):
        learned = word["learned"]
        return card(
            ft.Row(
                [
                    t(LANGUAGES.get(word["lang"], word["lang"]), 9, MUTED),
                    ft.Column(
                        [t(word["word"], 15, TEXT, ft.FontWeight.W_600),
                         t(word["translation"], 12, MUTED)],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    t("выучено" if learned else "учу", 10,
                      GREEN if learned else AMBER),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, icon_color=RED, tooltip="Удалить",
                        on_click=lambda e, wid=word["id"]: remove(e, wid),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
        )

    search = ft.TextField(
        value=STATE.get("search", ""),
        hint_text="Поиск слова или перевода",
        prefix_icon=ft.Icons.SEARCH,
        filled=True, bgcolor=CARD, border=field_border(),
        color=TEXT,
        on_change=lambda e: (STATE.update(search=e.control.value), fill_list()),
    )

    total = len(get_words(user_id, lang))
    fill_list()

    return ft.Column(
        [
            ft.Row(
                [
                    t("Словарь", 20, TEXT, ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    t(f"всего: {total}", 11, MUTED),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE, icon_color=GREEN, tooltip="Добавить слово",
                        on_click=lambda e: open_word_dialog(page),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    t("Язык", 11, MUTED),
                    ft.Container(content=language_selector(page), expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            search,
            words_list,
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


def open_word_dialog(page):
    """Диалог добавления нового слова на выбранном языке."""
    lang = STATE["user"].get("lang", "en")
    word_field = ft.TextField(label="Слово", autofocus=True, filled=True, bgcolor=CARD,
                              border=field_border(), color=TEXT)
    translation_field = ft.TextField(label="Перевод", filled=True, bgcolor=CARD,
                                     border=field_border(), color=TEXT)

    def save(e):
        try:
            add_word(STATE["user"]["id"], word_field.value,
                     translation_field.value, lang)
        except ValueError as exc:
            snack(page, str(exc), error=True)
            return
        page.pop_dialog()
        go_to(page, "dictionary")
        snack(page, "Слово добавлено")

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=CARD,
        title=t(f"Новое слово · {LANGUAGES.get(lang, lang)}", 18, TEXT,
                ft.FontWeight.BOLD),
        content=ft.Container(
            width=320,
            content=ft.Column([word_field, translation_field], spacing=10, tight=True),
        ),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.Button("Сохранить", on_click=save,
                              style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE)),
        ],
    )
    page.show_dialog(dialog)


# =============================================================================
#  12. ТРЕНИРОВКА
# =============================================================================
def view_training(page):
    """Меню режимов, текущий вопрос или итог тренировки."""
    if STATE["result"] is not None:
        return show_result(page)
    if STATE["questions"]:
        return show_question(page)

    descriptions = {
        "cards": "Посмотрите слово и отметьте, помните ли перевод",
        "choice": "Выберите правильный перевод из четырёх вариантов",
        "typing": "Напишите перевод слова вручную",
    }
    mode_cards = [
        card(
            ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_CIRCLE, color=ACCENT, size=26),
                    ft.Column(
                        [t(title, 15, TEXT, ft.FontWeight.W_600),
                         t(descriptions[mode], 10, MUTED, max_lines=2)],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED, size=18),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=lambda e, m=mode: start_training(page, m),
        )
        for mode, title in MODES.items()
    ]

    lang = STATE["user"].get("lang", "en")
    return ft.Column(
        [
            t("Тренировка", 20, TEXT, ft.FontWeight.BOLD),
            t(f"Язык: {LANGUAGES.get(lang, lang)} · "
              f"вопросов за подход: до {MAX_QUESTIONS}", 11, MUTED),
            *mode_cards,
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


def start_training(page, mode):
    """Создаёт новую тренировку и открывает первый вопрос."""
    try:
        questions = build_questions(
            STATE["user"]["id"], mode, STATE["user"].get("lang", "en"))
    except ValueError as exc:
        snack(page, str(exc), error=True)
        return

    STATE.update(mode=mode, questions=questions, index=0,
                 correct=0, feedback=None, result=None)
    go_to(page, "training")


def show_question(page):
    """Экран текущего вопроса."""
    question = STATE["questions"][STATE["index"]]
    total = len(STATE["questions"])
    mode = STATE["mode"]
    feedback = STATE["feedback"]
    is_flipped = STATE.get("flipped", False)

    def finish(e):
        STATE.update(questions=[], feedback=None, result=None, flipped=False)
        go_to(page, "training")

    def toggle_flip(e):
        if mode == "cards" and feedback is None:
            STATE["flipped"] = not is_flipped
            go_to(page, "training")

    header = ft.Row(
        [
            ft.TextButton("Выйти", on_click=finish,
                          style=ft.ButtonStyle(color=MUTED)),
            ft.Container(expand=True),
            t(f"Вопрос {STATE['index'] + 1} из {total}", 12, MUTED),
        ]
    )
    bar = ft.ProgressBar(
        value=STATE["index"] / total, bar_height=6, border_radius=4,
        color=ACCENT, bgcolor="#2A3157",
    )

    # Оформление карточки: в режиме cards её можно нажать, чтобы увидеть подсказку
    if mode == "cards":
        card_title = "ПОДСКАЗКА (нажмите, чтобы вернуть)" if is_flipped else "КАРТОЧКА (нажмите для подсказки)"
        card_text = mask_word(question["answer"]) if is_flipped else question["prompt"]
        card_bg = "#252D59" if is_flipped else CARD
        prompt = card(
            ft.Column(
                [
                    t(card_title, 10, ACCENT if is_flipped else MUTED),
                    t(card_text, 26, TEXT, ft.FontWeight.BOLD),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=card_bg,
            padding=24,
            on_click=toggle_flip if feedback is None else None,
        )
    else:
        prompt = card(
            ft.Column(
                [
                    t(MODES[mode], 10, MUTED),
                    t(question["prompt"], 26, TEXT, ft.FontWeight.BOLD),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=22,
        )

    if feedback is not None:
        color = GREEN if feedback["is_right"] else RED
        result_card = card(
            ft.Column(
                [
                    t("Верно!" if feedback["is_right"] else "Правильный ответ:",
                      14, color, ft.FontWeight.W_600),
                    t(question["answer"], 20, TEXT, ft.FontWeight.BOLD),
                    t(f"+{feedback['xp']} XP", 11, color),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#173D33" if feedback["is_right"] else "#3D1B27",
        )
        last = STATE["index"] + 1 >= total
        body = ft.Column(
            [
                result_card,
                ft.Button(
                    "Показать результат" if last else "Далее",
                    on_click=lambda e: next_question(page),
                    height=46, style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE),
                ),
            ],
            spacing=10,
        )
    elif mode in ("typing", "cards"):
        hint = "Введите иностранное слово" if mode == "cards" else "Введите перевод"
        answer = ft.TextField(
            hint_text=hint, autofocus=True, filled=True,
            bgcolor=CARD, border=field_border(), color=TEXT,
            on_submit=lambda e: submit_answer(page, e.control.value),
        )
        body = ft.Column(
            [
                answer,
                ft.Button(
                    "Проверить",
                    on_click=lambda e: submit_answer(page, answer.value),
                    height=46, style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE),
                ),
            ],
            spacing=10,
        )
    else:
        body = ft.Column(
            [
                ft.Button(
                    option, height=46,
                    on_click=lambda e, value=option: submit_answer(page, value),
                    style=ft.ButtonStyle(
                        bgcolor=CARD,
                        color=TEXT,
                        side=ft.BorderSide(1, "#2A3157"),
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                )
                for option in question["options"]
            ],
            spacing=8,
        )

    return ft.Column([header, bar, prompt, body],
                     spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)


def submit_answer(page, value):
    """Проверяет введённый ответ, обновляет прогресс слова и начисляет XP."""
    question = STATE["questions"][STATE["index"]]
    text = normalize(value)
    is_right = text != "" and text == normalize(question["answer"])

    update_word_progress(question["word_id"], is_right)
    if is_right:
        # Если в режиме карточек использовали подсказку, даём 5 XP вместо 10 XP
        gain = 5 if (STATE["mode"] == "cards" and STATE.get("flipped")) else 10
        STATE["correct"] += 1
    else:
        gain = 0

    STATE["user"]["xp"] = add_xp(STATE["user"]["id"], gain)
    STATE["feedback"] = {"is_right": is_right, "xp": gain}
    go_to(page, "training")


def next_question(page):
    """Следующий вопрос или завершение тренировки."""
    STATE["index"] += 1
    STATE["feedback"] = None
    STATE["flipped"] = False

    if STATE["index"] >= len(STATE["questions"]):
        user_id = STATE["user"]["id"]
        total = len(STATE["questions"])
        correct = STATE["correct"]
        xp = correct * 10
        save_result(user_id, MODES[STATE["mode"]], total, correct, xp)
        STATE["result"] = {"mode": STATE["mode"], "total": total,
                           "correct": correct, "xp": xp}
        STATE["questions"] = []
    go_to(page, "training")


def show_result(page):
    """Экран итогов тренировки."""
    result = STATE["result"]
    total = result["total"]
    accuracy = round(100 * result["correct"] / total) if total else 0
    color = GREEN if accuracy >= 80 else (AMBER if accuracy >= 50 else RED)

    def again(e):
        STATE["result"] = None
        start_training(page, STATE["mode"])

    def home(e):
        STATE["result"] = None
        go_to(page, "home")

    return ft.Column(
        [
            t("Тренировка завершена", 20, TEXT, ft.FontWeight.BOLD),
            card(
                ft.Column(
                    [
                        t(f"{accuracy}%", 42, color, ft.FontWeight.BOLD),
                        t("точность", 11, MUTED),
                        t(f"правильных: {result['correct']} из {total}", 12, TEXT),
                        t(f"получено опыта: +{result['xp']} XP", 12, AMBER),
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
            ),
            ft.Button("Ещё раз", on_click=again, height=46,
                              style=ft.ButtonStyle(bgcolor=ACCENT, color=ft.Colors.WHITE)),
            ft.OutlinedButton("На главную", on_click=home, height=44,
                              style=ft.ButtonStyle(color=ACCENT)),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


# =============================================================================
#  13. СТАТИСТИКА
# =============================================================================
def view_stats(page):
    """Статистика: цифры по языку и история тренировок из базы данных."""
    user = STATE["user"]
    lang = user.get("lang", "en")
    stats = get_stats(user["id"], lang)
    results = get_results(user["id"])
    level = level_of(user["xp"])

    def tile(label, value, color):
        return ft.Container(
            content=ft.Column(
                [t(value, 18, color, ft.FontWeight.BOLD), t(label, 10, MUTED)],
                spacing=2, tight=True,
            ),
            expand=True, bgcolor=CARD, border_radius=14, padding=10,
            border=ft.Border.all(1, "#2A3157"),
        )

    history = [
        card(
            ft.Row(
                [
                    ft.Column(
                        [t(row["mode"], 13, TEXT, ft.FontWeight.W_600),
                         t(row["created_at"].strftime("%d.%m.%Y %H:%M"), 9, MUTED)],
                        spacing=2, tight=True, expand=True,
                    ),
                    t(f"{row['correct']}/{row['total']}", 12, TEXT),
                    t(f"+{row['xp']} XP", 11, AMBER),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
        )
        for row in results
    ] or [t("Тренировок ещё не было", 12, MUTED)]

    return ft.Column(
        [
            t("Статистика", 20, TEXT, ft.FontWeight.BOLD),
            t(f"Язык: {LANGUAGES.get(lang, lang)}", 11, MUTED),
            ft.Row(
                [
                    tile("слов на языке", str(stats["total"]), TEXT),
                    tile("выучено", str(stats["learned"]), GREEN),
                ],
                spacing=8,
            ),
            ft.Row(
                [
                    tile("точность", f"{stats['accuracy']}%", AMBER),
                    tile("уровень", str(level), ACCENT),
                ],
                spacing=8,
            ),
            ft.Row(
                [
                    tile("верных ответов", str(stats["correct"]), GREEN),
                    tile("ошибок", str(stats["wrong"]), RED),
                ],
                spacing=8,
            ),
            t("Последние тренировки", 14, TEXT, ft.FontWeight.W_600),
            *history,
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


# =============================================================================
#  14. ПРОФИЛЬ
# =============================================================================
def view_profile(page):
    """Профиль: аккаунт, язык обучения и состояние базы данных."""
    user = STATE["user"]
    is_guest = user["username"] == "guest"

    def switch(e):
        STATE.update(user=None, questions=[], feedback=None, result=None)
        show_auth(page)

    db_info = "нет данных"
    try:
        rows = execute_query(
            "SELECT current_database() AS db, version() AS ver", fetch=True)
        if rows:
            db_info = f"{rows[0]['db']} · {rows[0]['ver'].split(',')[0]}"
    except Exception as exc:
        db_info = str(exc)

    return ft.Column(
        [
            t("Профиль", 20, TEXT, ft.FontWeight.BOLD),
            card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.PERSON, color=ACCENT, size=30),
                                ft.Column(
                                    [
                                        t(user["username"], 17, TEXT, ft.FontWeight.BOLD),
                                        t(f"Уровень {level_of(user['xp'])} · {user['xp']} XP",
                                          11, MUTED),
                                        t("гостевой режим" if is_guest else "аккаунт",
                                          10, AMBER if is_guest else GREEN),
                                    ],
                                    spacing=2, tight=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.ProgressBar(
                            value=(user["xp"] % XP_PER_LEVEL) / XP_PER_LEVEL,
                            bar_height=8, color=ACCENT, bgcolor="#2A3157",
                            border_radius=4,
                        ),
                    ],
                    spacing=10,
                )
            ),
            card(
                ft.Column(
                    [
                        t("Язык обучения", 13, TEXT, ft.FontWeight.W_600),
                        language_selector(page),
                    ],
                    spacing=8,
                )
            ),
            card(
                ft.Column(
                    [
                        t("База данных", 13, TEXT, ft.FontWeight.W_600),
                        t(f"Сервер: {DB_HOST}:{DB_PORT}", 11, MUTED),
                        t(f"База: {DB_NAME}", 11, MUTED),
                        t(f"Пользователь: {DB_USER}", 11, MUTED),
                        t(db_info, 11, GREEN, max_lines=2),
                        t("Все результаты хранятся в PostgreSQL", 10, MUTED),
                    ],
                    spacing=4,
                )
            ),
            ft.OutlinedButton(
                "Войти или зарегистрироваться" if is_guest else "Сменить аккаунт",
                on_click=switch, height=44,
                style=ft.ButtonStyle(color=RED if not is_guest else ACCENT),
            ),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


# =============================================================================
#  15. ЗАПУСК ПРИЛОЖЕНИЯ
# =============================================================================
def main(page):
    """Точка входа: настройка окна, создание базы, гостевой вход."""
    page.title = "TONgueNG — учите иностранные слова"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    try:
        page.window.width = 420
        page.window.height = 820
    except Exception:
        pass

    try:
        setup_database()
        STATE["user"] = guest_user()      # работаем без регистрации
    except Exception as exc:
        page.add(
            ft.Container(
                expand=True, bgcolor=BG, padding=24,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.STORAGE, color=RED, size=46),
                        t("Нет подключения к PostgreSQL", 20, TEXT, ft.FontWeight.BOLD),
                        t("Проверьте, что служба PostgreSQL запущена, а в начале "
                          "main.py указаны верные DB_USER и DB_PASSWORD.", 12, MUTED),
                        t(str(exc), 11, AMBER, max_lines=8),
                    ],
                    spacing=10,
                ),
            )
        )
        page.update()
        return

    go_to(page, "home")


if __name__ == "__main__":
    ft.run(main)
