# TEST LIVE - POUR PASSER EN VERT SUR RENDER
import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv('BOT_TOKEN', '')
VERSION = 'V2.7 TEST LIVE'

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'LIVE')
    def log_message(self, *a): pass

def start_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'{VERSION} EST EN LIVE ✅\n/ticket marche\n/bilan marche\nPrêt pour le vrai code V2.7')

async def bilan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('BILAN TEST: 88.8% - LIVE OK')

def main():
    start_server()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('ticket', ticket))
    app.add_handler(CommandHandler('bilan', bilan))
    app.add_handler(CommandHandler('start', ticket))
    print(f'{VERSION} lance - LIVE')
    app.run_polling()

if __name__ == '__main__':
    main()
