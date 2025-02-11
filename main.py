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

# /join Command
async def join(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    user_states[user.id] = "awaiting_join_response"
    await update.message.reply_text("Do you want to join? Please send a message explaining why.")
    
# Handle User Response for /join
async def handle_join_response(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    if user.id in user_states and user_states[user.id] == "awaiting_join_response":
        user_states.pop(user.id)  # Clear state
        # Forward the message to the admin group
        await context.bot.send_message(chat_id=GROUP_A_ID, text=f"Join request from {user.full_name}:\n{update.message.text}")
        await update.message.reply_text("Your request has been sent to the admins. Please wait for approval.")

# /leave Command
async def leave(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_member = await context.bot.get_chat_member(GROUP_P_ID, user.id)

    if chat_member.status in [ChatMember.LEFT, ChatMember.KICKED]:
        await update.message.reply_text("You have not joined yet!")
    else:
        user_states[user.id] = "awaiting_leave_reason"
        await update.message.reply_text("Please mention the reason why you want to leave.")

# Handle User Response for /leave
async def handle_leave_reason(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    if user.id in user_states and user_states[user.id] == "awaiting_leave_reason":
        user_states.pop(user.id)  # Clear state
        # Forward the message to the admin group
        await context.bot.send_message(chat_id=GROUP_A_ID, text=f"Leave request from {user.full_name}:\n{update.message.text}")
        await update.message.reply_text("Your leave request has been sent to the admins. Please wait for approval.")

# /cancel Command
async def cancel(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    if user.id in user_states:
        user_states.pop(user.id)
        await update.message.reply_text("Your current request has been canceled.")
    else:
        await update.message.reply_text("You have no ongoing requests.")

# /broadcast Command (Admin Only)
async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        return
    
    message = update.message.text.replace("/broadcast", "").strip()
    if not message:
        await update.message.reply_text("Usage: /broadcast [your message]")
        return

    for chat_id in user_states.keys():
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logging.warning(f"Failed to send message to {chat_id}: {e}")

    await update.message.reply_text("Broadcast message sent!")

# /about Command
async def about(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("This bot was created by bbb.")

# /help Command
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
    Available commands:
    /start - Start the bot
    /join - Request to join the group
    /leave - Request to leave the group
    /cancel - Cancel an ongoing request
    /broadcast - (Admins only) Send a message to all users
    /about - Information about the bot
    /help - Show this help message
    """
    await update.message.reply_text(help_text)

# Main bot function
def main():
    app = Application.builder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("star", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("broadcast", broadcast, filters.User(ADMIN_IDS)))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_join_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_leave_reason))

    app.run_polling()

# Run Flask and Telegram Bot in parallel
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask server in a new thread
    time.sleep(2)  # Delay to ensure Flask starts
    main()  # Start the bot
