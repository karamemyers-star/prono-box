TOKEN = "8808108179:AAEAm9ojlgS2HAhZNS3J8QdEp5zk70mFk5Q"

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot réveillé ✅ Envoie /ticket pour tester")

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Test OK, je suis vivant")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ticket", ticket))
app.run_polling()
