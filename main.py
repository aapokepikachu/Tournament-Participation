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
    await update.message.reply_text(f"Hi, {user.first_name}! I'm Cynthia, your assistant.")

async def ping(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id in ADMIN_IDS:
        start_time = time.time()
        msg = await update.message.reply_text("Pinging...")
        end_time = time.time()
        await msg.edit_text(f"Pong! Response time: {round((end_time - start_time) * 1000)}ms")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

async def join(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Check if user is already in Group P
    chat_member = await context.bot.get_chat_member(GROUP_P_ID, user_id)
    if chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("You are already participating!")
        return

    user_states[user_id] = "waiting_for_join_response"
    await update.message.reply_text("Do you want to join? Please reply with your reason.")

async def handle_join_response(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_states and user_states[user_id] == "waiting_for_join_response":
        user_states.pop(user_id)  # Clear state

        # Forward message to Group A
        await context.bot.send_message(GROUP_A_ID, f"Join request from {update.message.from_user.full_name} ({user_id}): {update.message.text}")
        await update.message.reply_text("Your request has been sent to admins. Please wait for approval.")

async def leave(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Check if user is in Group P
    chat_member = await context.bot.get_chat_member(GROUP_P_ID, user_id)
    if chat_member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("You have not joined yet!")
        return

    user_states[user_id] = "waiting_for_leave_reason"
    await update.message.reply_text("Mention the reason why you want to exit.")

async def handle_leave_reason(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_states and user_states[user_id] == "waiting_for_leave_reason":
        user_states.pop(user_id)  # Clear state

        # Forward leave reason to Group A
        await context.bot.send_message(GROUP_A_ID, f"Leave request from {update.message.from_user.full_name} ({user_id}): {update.message.text}")
        await update.message.reply_text("Please wait for the admins' approval.")

async def cancel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        await update.message.reply_text("Process canceled.")
    else:
        await update.message.reply_text("No active process to cancel.")

async def send(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /send <user_id>")
            return
        
        user_id = int(args[0])
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a message to send it.")
            return
        
        msg_text = update.message.reply_to_message.text
        await context.bot.send_message(user_id, msg_text)
        await update.message.reply_text("Message sent successfully.")

    except Exception as e:
        await update.message.reply_text("This message failed to send.")
        logging.error(f"Failed to send message: {e}")

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        return
    
    message = update.message.text.replace("/broadcast", "").strip()
    if not message:
        await update.message.reply_text("Usage: /broadcast [your message]")
        return

    for chat_id in user_states.keys():
        try:
            await context.bot.send_message(chat_id, message)
        except Exception as e:
            logging.warning(f"Failed to send message to {chat_id}: {e}")

    await update.message.reply_text("Broadcast message sent!")

async def about(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("This bot was created by bbb.")

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
Available commands:
- /start or /star - Greet the user.
- /join - Request to join the group.
- /leave - Request to leave the group.
- /cancel - Cancel an ongoing request.
- /send <user_id> (Admins) - Send a message to a user.
- /broadcast (Admins) - Send a message to all users.
- /ping (Admins) - Check bot response time.
- /about - Show bot creator info.
- /help - List available commands.
"""
    await update.message.reply_text(help_text)

def main():
    app = Application.builder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("star", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("broadcast", broadcast, filters.User(ADMIN_IDS)))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_join_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_leave_reason))

    logging.info("Bot is running!")
    app.run_polling()

# Run Flask and Telegram Bot in parallel
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask server in a new thread
    time.sleep(2)  # Delay to ensure Flask starts
    main()  # Start the bot
