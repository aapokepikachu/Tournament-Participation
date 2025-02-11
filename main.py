import logging
import threading
import time
from flask import Flask
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TOKEN, GROUP_A_ID, GROUP_P_ID, ADMIN_IDS  # Import config values

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Dictionary to store user states
user_states = {}

# Initialize Flask app (Fake Web Server for Render)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    app.run(host="0.0.0.0", port=5000)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"Hi, {user.first_name}! It's nice to meet you. I am Cynthia, your assistant.")

# Main bot function
def main():
    app = Application.builder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("star", start))
    # (Add all other handlers here...)

    app.run_polling()

# Run Flask and Telegram Bot in parallel
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask server in a new thread
    time.sleep(2)  # Delay to ensure Flask starts
    main()  # Start the bot
