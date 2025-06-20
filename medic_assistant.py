import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
from langdetect import detect

# 🔐 Pakrauna API raktus
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 🧠 Sistema prompt
SYSTEM_PROMPT = """
⚠️ SVARBU: Šis dirbtinis intelektas yra skirtas tik švietimo tikslams. Jis nepakeičia gydytojo...
"""

def detect_language(text):
    try:
        return detect(text)
    except:
        return "lt"

def start(update: Update, context: CallbackContext):
    greeting = (
        "👋 Sveikas! Aš esu *Medic Assistant* – tavo mokymosi pagalbininkas.\n\n"
        "Galimos komandos:\n"
        "/case – gauti klinikinį atvejį\n"
        "/studyplan – mokymosi planas\n"
        "/explain – paaiškinti metodą\n"
        "/resetcontext – išvalyti kontekstą\n\n"
        "Arba užduok klausimą."
    )
    update.message.reply_text(greeting, parse_mode='Markdown')

def case(update: Update, context: CallbackContext):
    update.message.reply_text("🩺 Įrašyk klinikinio atvejo tipą (pvz., hepatitas)")

def studyplan(update: Update, context: CallbackContext):
    update.message.reply_text("📚 Įrašyk temą, kuriam nori pasiruošti")

def explain(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Įrašyk metodą ar sąvoką paaiškinimui")

def resetcontext(update: Update, context: CallbackContext):
    update.message.reply_text("♻️ Kontekstas išvalytas!")

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    lang = detect_language(user_message)
    lang_prompt = {
        "lt": "Atsakyk lietuviškai.",
        "en": "Respond in English.",
        "ru": "Ответь по-русски.",
        "pl": "Odpowiedz po polsku."
    }.get(lang, "Atsakyk lietuviškai.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"{lang_prompt} {SYSTEM_PROMPT}"},
                {"role": "user",   "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        reply_text = response.choices[0].message["content"]
        update.message.reply_text(reply_text)
    except Exception as e:
        update.message.reply_text(f"⚠️ Klaida: {e}")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("case", case))
    dp.add_handler(CommandHandler("studyplan", studyplan))
    dp.add_handler(CommandHandler("explain", explain))
    dp.add_handler(CommandHandler("resetcontext", resetcontext))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Medic Assistant veikia. Eik į Telegram ir pradėk pokalbį.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
from langdetect import detect

# 🔐 Pakrauna API raktus
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 🧠 Sistema prompt
SYSTEM_PROMPT = """
⚠️ SVARBU: Šis dirbtinis intelektas yra skirtas tik švietimo tikslams. Jis nepakeičia gydytojo...
"""

def detect_language(text):
    try:
        return detect(text)
    except:
        return "lt"

def start(update: Update, context: CallbackContext):
    greeting = (
        "👋 Sveikas! Aš esu *Medic Assistant* – tavo mokymosi pagalbininkas.\n\n"
        "Galimos komandos:\n"
        "/case – gauti klinikinį atvejį\n"
        "/studyplan – mokymosi planas\n"
        "/explain – paaiškinti metodą\n"
        "/resetcontext – išvalyti kontekstą\n\n"
        "Arba užduok klausimą."
    )
    update.message.reply_text(greeting, parse_mode='Markdown')

def case(update: Update, context: CallbackContext):
    update.message.reply_text("🩺 Įrašyk klinikinio atvejo tipą (pvz., hepatitas)")

def studyplan(update: Update, context: CallbackContext):
    update.message.reply_text("📚 Įrašyk temą, kuriam nori pasiruošti")

def explain(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Įrašyk metodą ar sąvoką paaiškinimui")

def resetcontext(update: Update, context: CallbackContext):
    update.message.reply_text("♻️ Kontekstas išvalytas!")

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    lang = detect_language(user_message)
    lang_prompt = {
        "lt": "Atsakyk lietuviškai.",
        "en": "Respond in English.",
        "ru": "Ответь по-русски.",
        "pl": "Odpowiedz po polsku."
    }.get(lang, "Atsakyk lietuviškai.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"{lang_prompt} {SYSTEM_PROMPT}"},
                {"role": "user",   "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        reply_text = response.choices[0].message["content"]
        update.message.reply_text(reply_text)
    except Exception as e:
        update.message.reply_text(f"⚠️ Klaida: {e}")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("case", case))
    dp.add_handler(CommandHandler("studyplan", studyplan))
    dp.add_handler(CommandHandler("explain", explain))
    dp.add_handler(CommandHandler("resetcontext", resetcontext))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Medic Assistant veikia. Eik į Telegram ir pradėk pokalbį.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()



    
