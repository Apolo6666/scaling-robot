import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from langdetect import detect

# 🔐 Pakrauna API raktus iš .env failo
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔑 Sukuriamas OpenAI klientas
client = OpenAI(api_key=OPENAI_API_KEY)

# 🧠 Sistema prompt – boto vaidmuo
SYSTEM_PROMPT = """
⚠️ SVARBU: Šis dirbtinis intelektas yra skirtas tik švietimo tikslams. Jis nepakeičia gydytojo, negali nustatyti diagnozės, nesiūlo gydymo ir nėra medicininė priemonė.

Tu esi „Medic Assistant“ – išmanus mokymosi asistentas, padedantis medicinos studentui Lietuvoje. Tu paaiškini laboratorinius tyrimus, simptomus ir diagnostikos algoritmus. Visi atsakymai turi būti aiškūs, profesionalūs, paremti recenzuotais šaltiniais (PubMed, UpToDate, Cochrane, SAM.lt). Tu niekada neteiki klinikinių sprendimų – tik mokymo tikslais.
"""

# 🌐 Kalbos nustatymas
def detect_language(text):
    try:
        return detect(text)
    except:
        return "lt"

# 🚀 Komanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = (
        "👋 Sveikas! Aš esu *Medic Assistant* – tavo mokymosi pagalbininkas.\n\n"
        "Galimos komandos:\n"
        "/case – gauti mokomąjį klinikinį atvejį\n"
        "/studyplan – sudaryti mokymosi planą\n"
        "/explain – paaiškinti medicininį metodą\n"
        "/resetcontext – išvalyti kontekstą\n\n"
        "Arba tiesiog užduok klausimą – atsakysiu pasirinktąja kalba."
    )
    await update.message.reply_text(greeting, parse_mode='Markdown')

# 📚 Komanda /case
async def case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🩺 Įvesk norimą klinikinio atvejo tipą (pvz.: kvėpavimo takų infekcija, hepatitas ir pan.)")

# 📘 Komanda /studyplan
async def studyplan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Įrašyk temą ar egzaminą, kuriam nori pasiruošti – padėsiu sudaryti planą.")

# 🔬 Komanda /explain
async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Įrašyk metodą ar sąvoką, kurią reikia paaiškinti.")

# 🔄 Komanda /resetcontext
async def resetcontext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Kontekstas išvalytas. Galime pradėti nuo pradžių!")

# 💬 Žinučių apdorojimas
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = detect_language(user_message)

    lang_prompt = {
        "lt": "Atsakyk lietuviškai.",
        "en": "Respond in English.",
        "ru": "Ответь по-русски.",
        "pl": "Odpowiedz po polsku."
    }.get(lang, "Atsakyk lietuviškai.")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"{lang_prompt} {SYSTEM_PROMPT}"},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Klaida: {str(e)}")

# 🧭 Paleidimas
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("case", case))
    app.add_handler(CommandHandler("studyplan", studyplan))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("resetcontext", resetcontext))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Medic Assistant veikia. Eik į Telegram ir pradėk pokalbį.")
    app.run_polling()

    