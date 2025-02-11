import logging
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TOKEN, GROUP_A_ID, GROUP_P_ID, ADMIN_IDS  # Import config values

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Dictionary to store user states
user_states = {}

async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"Hi, {user.first_name}! It's nice to meet you. I am Cynthia, your assistant.")

# (Rest of your bot logic remains unchanged...)

def main():
    app = Application.builder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("star", start))
    # (Add all other handlers here...)

    app.run_polling()

if __name__ == "__main__":
    main()
