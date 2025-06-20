import os
import logging
from dotenv import load_dotenv
from langdetect import detect
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI  # naujas klientas 1.x

# ── Aplinkos kintamieji ───────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
⚠️ Šis DI skirtas tik mokymuisi. Nediagnozuoja ir neskiria gydymo.
Tu esi „Medic Assistant“ – aiškini laboratorinius tyrimus, simptomus, diagnostikos algoritmus;
remiesi PubMed, UpToDate, Cochrane, SAM.lt; jokios klinikinės rekomendacijos.
"""

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")

# ── Pagalbinės funkcijos ──────────────────────────────────────────────
def detect_language(text: str) -> str:
    try:
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

async def ask_openai(user_msg: str, code: str) -> str:
    """Kreipiasi į OpenAI naudodamas naują 1.x sintaksę."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",           # turi veikti su tavo raktu; keisk, jei reikia
        messages=[
            {"role": "system", "content": f"{lang_prompt(code)} {SYSTEM_PROMPT}"},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.5,
        max_tokens=1500,
    )
    return resp.choices[0].message.content

# ── Komandos ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Sveikas! Aš – *Medic Assistant*.\n\n"
        "/case – klinikinis atvejis\n"
        "/studyplan – mokymosi planas\n"
        "/explain – paaiškinti metodą\n"
        "/resetcontext – išvalyti kontekstą",
        parse_mode="Markdown",
    )

async def case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🩺 Įrašyk atvejo tipą (pvz. hepatitas)")

async def studyplan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Įrašyk temą – sudarysiu planą")

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Įrašyk metodą ar sąvoką")

async def resetcontext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Kontekstas išvalytas!")

# ── Žinučių apdorojimas ───────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    code = detect_language(user_msg)
    try:
        reply = await ask_openai(user_msg, code)
        await update.message.reply_text(reply)
    except Exception as e:
        logging.exception("OpenAI klaida")
        await update.message.reply_text(f"⚠️ Klaida: {e}")

# ── Paleidimas ────────────────────────────────────────────────────────
async def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .concurrent_updates(True)  # PTB 22.x rekomenduojama
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("case", case))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("resetcontext", resetcontext))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Medic Assistant veikia – rašyk /start Telegram’e.")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())







    
