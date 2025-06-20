import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
import openai
from langdetect import detect

# 🔐 Aplinkos kintamieji
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = """
⚠️ SVARBU: Šis DI skirtas tik mokymuisi. Nediagnozuoja ir neskiria gydymo.
Tu esi „Medic Assistant“ – aiškini laboratorinius tyrimus bei diagnostiką, remiesi PubMed/UpToDate/Cochrane.
"""

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "lt"

# ── Komandos ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Sveikas! Aš esu *Medic Assistant* – tavo mokymosi pagalbininkas.\n\n"
        "/case – klinikinis atvejis\n"
        "/studyplan – mokymosi planas\n"
        "/explain – paaiškinti metodą\n"
        "/resetcontext – išvalyti kontekstą",
        parse_mode="Markdown",
    )

async def case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🩺 Įrašyk norimą atvejo tipą (pvz. hepatitas)")

async def studyplan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Įrašyk temą – sudarysiu planą")

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Įrašyk metodą ar sąvoką")

async def resetcontext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Kontekstas išvalytas!")

# ── Žinutės ────────────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    lang = detect_language(user_msg)
    lang_prompt = {
        "lt": "Atsakyk lietuviškai.",
        "en": "Respond in English.",
        "ru": "Ответь по-русски.",
        "pl": "Odpowiedz po polsku."
    }.get(lang, "Atsakyk lietuviškai.")

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"{lang_prompt} {SYSTEM_PROMPT}"},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.5,
            max_tokens=1500,
        )
        await update.message.reply_text(resp.choices[0].message["content"])
    except Exception as e:
        await update.message.reply_text(f"⚠️ Klaida: {e}")

# ── Paleidimas ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("case", case))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("resetcontext", resetcontext))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Medic Assistant veikia – gali rašyti /start Telegram’e.")
    app.run_polling()




    
