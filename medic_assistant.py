"""
Telegram bot: Medic Assistant
– Prenumeratos planai, dienos limitai ir funkcijų apribojimai
– Administratoriai (ADMIN_IDS) nepatenka į limitus
Autorė: Generated with ChatGPT o3, 2025-06-20 (merged version)
"""

import os
import logging
import datetime as dt
import feedparser
from dotenv import load_dotenv
from telegram import (
    Update,
    InputFile,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from openai import OpenAI
from fpdf import FPDF

# ─────────────────────────── Environment ───────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ───────────────────────────── Admins ──────────────────────────────
ADMIN_IDS: list[int] = [712878075]  # ← įrašykite kitus administratorių ID, jei reikia

# ───────────────────────────── Constants ───────────────────────────
SYSTEM_PROMPT = (
    "\n⚠️ Šis DI skirtas tik mokymuisi. "
    "Tu esi ‘Medic Assistant’ – aiškini laboratorinius tyrimus, simptomus, diagnostikos algoritmus; "
    "remiesi PubMed, UpToDate, Cochrane, SAM.lt; jokios klinikinės rekomendacijos."
)

PROFILE_LANGUAGE, PROFILE_COUNTRY, PROFILE_LEVEL, QUIZ_TOPIC, SIM_SYMPTOMS, FLASH_TOPIC, ANSWER_STATE = range(7)

# Subscription tiers: 0=Free,1=Basic,2=Pro Student,3=Premium MedTech
TIER_NAMES: list[str] = [
    "🟢 Free (1 užklausa/d., be PDF)",
    "🔵 Basic (5 užklausos/d.)",
    "🟣 Pro Student (neribota, PDF, testai, flashcards)",
    "🔴 Premium MedTech (viskas + paveikslų analizė, grupės)",
]
TIER_DAILY_QUOTA = {0: 1, 1: 5, 2: None, 3: None}  # None = unlimited
FEATURE_MIN_TIER = {
    "pdf": 2,
    "flashcards": 2,
    "image_analysis": 3,
    "rooms": 3,
}

# ───────────────────────────── Globals ─────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
user_progress: dict[int, int] = {}            # viso užklausų
user_daily_usage: dict[int, dict[str, int]] = {}  # {'date': YYYY-MM-DD, 'count': n}
rooms: dict[str, list[int]] = {}
user_tiers: dict[int, int] = {}               # default → Free

# ──────────────────────── Helper functions ─────────────────────────
def detect_language(text: str) -> str:
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "lt"


def lang_prompt(code: str) -> str:
    return {
        "lt": "Atsakyk lietuviškai.",
        "en": "Respond in English.",
        "ru": "Ответь по-русски.",
        "pl": "Odpowiedz po polsku.",
    }.get(code, "Atsakyk lietuviškai.")


def today_str() -> str:
    return dt.date.today().isoformat()


def increment_usage(user_id: int) -> bool:
    """Padidina dienos skaitiklį. Grąžina True, jei dar nepasiektas limitas / admin / neribota."""
    if user_id in ADMIN_IDS:
        return True
    tier = user_tiers.get(user_id, 0)
    quota = TIER_DAILY_QUOTA[tier]
    if quota is None:
        return True
    record = user_daily_usage.setdefault(user_id, {"date": today_str(), "count": 0})
    if record["date"] != today_str():
        record["date"] = today_str()
        record["count"] = 0
    if record["count"] >= quota:
        return False
    record["count"] += 1
    return True


def has_feature(user_id: int, feature: str) -> bool:
    if user_id in ADMIN_IDS:
        return True
    return user_tiers.get(user_id, 0) >= FEATURE_MIN_TIER.get(feature, 0)


def save_as_pdf(text: str, filename: str = "document.pdf") -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    path = f"/tmp/{filename}"
    pdf.output(path)
    return path


async def ask_openai(user_msg: str, lang_code: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"{lang_prompt(lang_code)} {SYSTEM_PROMPT}"},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
        max_tokens=1500,
    )
    return resp.choices[0].message.content

# ──────────────────────────── Commands ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Sveikas! Aš – *Medic Assistant*.", parse_mode="Markdown")
    await update.message.reply_text(
        "Komandos:\n"
        "/start, /profile, /quiz, /answer, /review, /export_pdf, /export_test, "
        "/flashcards, /method, /guideline, /simpatient, /progress, /progress_pdf, "
        "/subscription_status, /upgrade, /create_room, /join_room, /list_rooms, /resetcontext"
    )

# Prenumerata
async def subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tier = user_tiers.get(update.effective_user.id, 0)
    await update.message.reply_text(f"🔐 Tavo planas: {TIER_NAMES[tier]}")


async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔼 Norėdamas atnaujinti prenumeratą:\n"
        "1️⃣ Apsilankyk: https://your-payment-link.com\n"
        "2️⃣ Po apmokėjimo parašyk /subscription_status – suteiksime prieigas",
        disable_web_page_preview=True,
    )

# Profilis
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pasirink kalbą:",
        reply_markup=ReplyKeyboardMarkup([["lt", "en"], ["ru", "pl"]], one_time_keyboard=True),
    )
    return PROFILE_LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("profile", {})["language"] = update.message.text.lower()
    await update.message.reply_text(
        "Pasirink šalį:",
        reply_markup=ReplyKeyboardMarkup([["lt", "uk"], ["us", "de"]], one_time_keyboard=True),
    )
    return PROFILE_COUNTRY


async def set_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile"]["country"] = update.message.text.lower()
    await update.message.reply_text(
        "Pasirink lygį:",
        reply_markup=ReplyKeyboardMarkup([["studentas", "gydytojas", "mokslininkas"]], one_time_keyboard=True),
    )
    return PROFILE_LEVEL


async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile"]["level"] = update.message.text.lower()
    await update.message.reply_text(f"✅ Profilis nustatytas: {context.user_data['profile']}",
                                    reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def resetcontext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("♻️ Kontekstas išvalytas!")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Nutraukta.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Method info
async def method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 Įrašyk medicininį metodą, kurį nori suprasti.")

# Quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧪 Įrašyk testavimo temą:")
    return QUIZ_TOPIC


async def receive_quiz_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not increment_usage(update.effective_user.id):
        return await quota_exceeded(update, context)
    topic = update.message.text.strip()
    level = context.user_data.get("profile", {}).get("level", "studentas")
    prompt = (
        f"Sukurk 3 pasirenkamo atsakymo klausimus ({level} lygiui) apie: {topic}. "
        "Formatuok su pažymėtais atsakymais A), B), C). Prie teisingo atsakymo pridėk ✅."
    )
    lang = context.user_data.get("profile", {}).get("language", detect_language(topic))
    questions = await ask_openai(prompt, lang)
    context.user_data["last_quiz"] = {"topic": topic, "content": questions}
    user_progress[update.effective_user.id] = user_progress.get(update.effective_user.id, 0) + 1
    await update.message.reply_text(f"🧠 Klausimai apie '{topic}':\n\n{questions}")
    return ConversationHandler.END


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "last_quiz" not in context.user_data:
        await update.message.reply_text("❗ Su /quiz sukurk testą.")
        return ConversationHandler.END
    await update.message.reply_text("✏️ Įvesk savo atsakymus A/B/C, pvz.: A B C")
    return ANSWER_STATE


async def receive_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not increment_usage(update.effective_user.id):
        return await quota_exceeded(update, context)
    ans = update.message.text.strip()
    quiz = context.user_data["last_quiz"]["content"]
    prompt = f"Tekstas su ✅ teisingais atsakymais: {quiz} Vartotojo atsakymai: {ans}. Įvertink ir paaiškink."
    lang = context.user_data.get("profile", {}).get("language", detect_language(ans))
    result = await ask_openai(prompt, lang)
    await update.message.reply_text(f"📝 Vertinimas:\n{result}")
    return ConversationHandler.END


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "last_quiz" in context.user_data:
        q = context.user_data["last_quiz"]
        await update.message.reply_text(f"🔁 Testas apie '{q['topic']}':\n\n{q['content']}")
    else:
        await update.message.reply_text("❗ Nėra testo.")

# Export PDF (tier ≥2)
async def export_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "pdf"):
        return await restricted_feature(update, context, "pdf")
    if "last_reply" in context.user_data:
        path = save_as_pdf(context.user_data["last_reply"], "reply.pdf")
        await update.message.reply_document(InputFile(path))
    else:
        await update.message.reply_text("❗ Nėra atsakymo.")


async def export_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "pdf"):
        return await restricted_feature(update, context, "pdf")
    if "last_quiz" in context.user_data:
        q = context.user_data["last_quiz"]
        text = f"Tema: {q['topic']}\n\n{q['content']}"
        path = save_as_pdf(text, "testas.pdf")
        await update.message.reply_document(InputFile(path))
    else:
        await update.message.reply_text("❗ Nėra testo.")

# Flashcards (tier ≥2)
async def flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "flashcards"):
        return await restricted_feature(update, context, "flashcards")
    await update.message.reply_text("📚 Įrašyk temą flashcards:")
    return FLASH_TOPIC


async def receive_flash_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not increment_usage(update.effective_user.id):
        return await quota_exceeded(update, context)
    top = update.message.text.strip()
    lang = context.user_data.get("profile", {}).get("language", detect_language(top))
    prompt = f"Sukurk 5 flashcards tema: {top}, klausimas ir trumpas atsakymas."
    rc = await ask_openai(prompt, lang)
    await update.message.reply_text(f"🧠 Flashcards:\n\n{rc}")
    return ConversationHandler.END

# Simulated patient
async def simpatient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Įrašyk simptomus:")
    return SIM_SYMPTOMS


async def receive_symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not increment_usage(update.effective_user.id):
        return await quota_exceeded(update, context)
    sym = update.message.text.strip()
    lang = context.user_data.get("profile", {}).get("language", detect_language(sym))
    prompt = f"Remdamasis simptomais: {sym}, sukurk klinikinį atvejį su anamneze, tyrimais, diagnozę."
    case = await ask_openai(prompt, lang)
    await update.message.reply_text(f"📋 Atvejis:\n\n{case}")
    return ConversationHandler.END

# Guidelines feed
async def guideline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed = feedparser.parse("https://www.ecdc.europa.eu/en/latest-news/rss")
    items = feed["entries"][:3]
    msg = "📑 Naujausios ECDC gairės:\n" + "\n".join(f"- {i.title}: {i.link}" for i in items)
    await update.message.reply_text(msg)

# Progress
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cnt = user_progress.get(uid, 0)
    await update.message.reply_text(f"📊 Užklausų (viso): {cnt}")


async def progress_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "pdf"):
        return await restricted_feature(update, context, "pdf")
    uid = update.effective_user.id
    cnt = user_progress.get(uid, 0)
    txt = f"Naudotojo ID: {uid}\nUžklausos (viso): {cnt}"
    path = save_as_pdf(txt, "progress.pdf")
    await update.message.reply_document(InputFile(path))

# Rooms (tier ≥3)
async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "rooms"):
        return await restricted_feature(update, context, "rooms")
    room = " ".join(context.args)
    if not room:
        return await update.message.reply_text("❗ Nurodyk kambario pavadinimą.")
    rooms.setdefault(room, []).append(update.effective_user.id)
    await update.message.reply_text(f"✅ Kambarys sukurtas: {room}")


async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "rooms"):
        return await restricted_feature(update, context, "rooms")
    room = " ".join(context.args)
    if room in rooms:
        rooms[room].append(update.effective_user.id)
        await update.message.reply_text(f"✅ Prisijungei: {room}")
    else:
        await update.message.reply_text("❗ Nėra kambario")


async def list_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "rooms"):
        return await restricted_feature(update, context, "rooms")
    if rooms:
        await update.message.reply_text("📋 Kambariai:\n" + "\n".join(rooms.keys()))
    else:
        await update.message.reply_text("❗ Nėra kambarių")

# Image analysis (tier ≥3)
async def image_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_feature(update.effective_user.id, "image_analysis"):
        return await restricted_feature(update, context, "image_analysis")
    if not update.message.photo:
        return await update.message.reply_text("❗ Siųsk nuotrauką")
    file = await update.message.photo[-1].get_file()
    path = f"/tmp/{file.file_id}.jpg"
    await file.download_to_drive(path)
    analysis = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analizuok medicininę nuotrauką."},
            {"role": "user", "content": f"Atvaizdas: {path}"},
        ],
    )
    await update.message.reply_text(analysis.choices[0].message.content)

# Generic message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not increment_usage(update.effective_user.id):
        return await quota_exceeded(update, context)
    user_msg = update.message.text
    lang_code = context.user_data.get("profile", {}).get("language", detect_language(user_msg))
    user_progress[update.effective_user.id] = user_progress.get(update.effective_user.id, 0) + 1
    reply = await ask_openai(user_msg, lang_code)
    context.user_data["last_reply"] = reply
    await update.message.reply_text(reply)

# ──────────────────────────── Helpers ──────────────────────────────
async def quota_exceeded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tier = user_tiers.get(update.effective_user.id, 0)
    quota = TIER_DAILY_QUOTA[tier]
    await update.message.reply_text(
        f"🚦 Viršyta dienos riba ({quota} užklausa). Atnaujink planą su /upgrade arba bandyk rytoj."
    )


async def restricted_feature(update: Update, context: ContextTypes.DEFAULT_TYPE, feature: str):
    min_tier = FEATURE_MIN_TIER[feature]
    await update.message.reply_text(
        f"🔒 Ši funkcija prieinama nuo {TIER_NAMES[min_tier]}. Naudok /upgrade."
    )

# ─────────────────────────── Main entry ───────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    # Conversation handlers
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("profile", profile)],
        states={
            PROFILE_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            PROFILE_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_country)],
            PROFILE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_level)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz)],
        states={QUIZ_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quiz_topic)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("answer", answer)],
        states={ANSWER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answers)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("flashcards", flashcards)],
        states={FLASH_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_flash_topic)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("simpatient", simpatient)],
        states={SIM_SYMPTOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_symptoms)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    # Simple command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("export_pdf", export_pdf))
    app.add_handler(CommandHandler("export_test", export_test))
    app.add_handler(CommandHandler("method", method))
    app.add_handler(CommandHandler("guideline", guideline))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("progress_pdf", progress_pdf))
    app.add_handler(CommandHandler("subscription_status", subscription_status))
    app.add_handler(CommandHandler("upgrade", upgrade))
    app.add_handler(CommandHandler("create_room", create_room))
    app.add_handler(CommandHandler("join_room", join_room))
    app.add_handler(CommandHandler("list_rooms", list_rooms))
    app.add_handler(CommandHandler("resetcontext", resetcontext))

    # Message / photo handlers
    app.add_handler(MessageHandler(filters.PHOTO, image_analysis))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Medic Assistant veikia su prenumeratomis + admin išimtimis.")
    app.run_polling(drop_pending_updates=True)









    
