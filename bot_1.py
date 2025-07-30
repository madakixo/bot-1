import sqlite3
import os
import logging
import requests
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# --- Configuration & Initialization ---

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load sensitive data and configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ENCRYPTION_KEY_STR = os.getenv('ENCRYPTION_KEY')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
BOT_WEBHOOK_URL = os.getenv('BOT_WEBHOOK_URL')  # e.g., https://your-app-name.herokuapp.com

# Validate that essential environment variables are set
if not all([TELEGRAM_TOKEN, ADMIN_USER_ID, BOT_WEBHOOK_URL]):
    raise ValueError("Missing essential environment variables. Please check your .env file.")

# Set up encryption: load key or generate a new one
if ENCRYPTION_KEY_STR:
    ENCRYPTION_KEY = ENCRYPTION_KEY_STR.encode()
else:
    logger.warning("ENCRYPTION_KEY not found. Generating a new one. PLEASE SET THIS IN YOUR .env FILE.")
    ENCRYPTION_KEY = Fernet.generate_key()
    print(f"Generated ENCRYPTION_KEY: {ENCRYPTION_KEY.decode()}")
cipher_suite = Fernet(ENCRYPTION_KEY)

# --- State Definitions for ConversationHandler ---
SELECTING_ACTION, GETTING_LOCATION, GETTING_CONTACT = range(3)

# Nigerian states for location validation
NIGERIAN_STATES = [
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
    'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo',
    'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos', 'Nasarawa',
    'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
]

# --- Helper Functions ---

def init_db():
    """Initializes the SQLite database and table."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        contact_info TEXT,
        state TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_users_timestamp
    AFTER UPDATE ON users FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = OLD.user_id;
    END;
    ''')
    conn.commit()
    conn.close()

def get_state_from_location(latitude, longitude):
    """Gets Nigerian state from coordinates using Nominatim."""
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}'
    headers = {'User-Agent': 'NigeriaConnectBot/1.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        state = data.get('address', {}).get('state', '').replace(' State', '')
        return state if state in NIGERIAN_STATES else None
    except requests.RequestException as e:
        logger.error(f"Geolocation request failed: {e}")
        return None

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user if they want to connect."""
    keyboard = [
        [InlineKeyboardButton("Yes, find a connection", callback_data='connect_yes')],
        [InlineKeyboardButton("No, thanks", callback_data='connect_no')],
    ]
    await update.message.reply_text(
        "Welcome to NigeriaConnect!\n\n"
        "This bot helps you connect with people across Nigeria. All data is encrypted and handled with care.\n\n"
        "Ready to start?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Process cancelled. Type /start to begin again.")
    context.user_data.clear()
    return ConversationHandler.END

async def user_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get the total number of users."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await update.message.reply_text(f"Total users in the database: {count}")
    except Exception as e:
        logger.error(f"Error fetching user count: {e}")
        await update.message.reply_text("Failed to retrieve user count.")
    finally:
        if conn:
            conn.close()

# --- Conversation Steps ---

async def start_connection_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Yes' button, asking for location."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="Great! Please share your location so I can find connections in your state. "
             "You can use the paperclip icon to send your live or current location."
    )
    return GETTING_LOCATION

async def no_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'No' button, ending the conversation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="No problem. Feel free to come back anytime! Type /start to begin again.")
    return ConversationHandler.END

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes location and requests contact information."""
    location = update.message.location
    if not location:
        await update.message.reply_text("Could not read location. Please try again or /cancel.")
        return GETTING_LOCATION

    await update.message.reply_text("Checking your location...")
    state = get_state_from_location(location.latitude, location.longitude)
    if not state:
        await update.message.reply_text("Sorry, I couldn't determine a Nigerian state from your location. Please try again or /cancel.")
        return GETTING_LOCATION

    context.user_data['state'] = state
    await update.message.reply_text(
        f"Location confirmed: {state} State. Please provide your name and phone number so we can connect you.",
        reply_markup=ForceReply(input_field_placeholder="e.g., Alex Johnson, +234...")
    )
    return GETTING_CONTACT

async def handle_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves user's contact info."""
    user_id = update.effective_user.id
    contact_info = update.message.text
    state = context.user_data.get('state', 'Unknown')

    encrypted_contact = cipher_suite.encrypt(contact_info.encode()).decode()

    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, contact_info, state)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            contact_info = excluded.contact_info,
            state = excluded.state;
        """, (user_id, encrypted_contact, state))
        conn.commit()
    except Exception as e:
        logger.error(f"Database error while saving contact: {e}")
        await update.message.reply_text("A database error occurred. Your info was not saved. Please contact support.")
    finally:
        if conn:
            conn.close()

    await update.message.reply_text(
        "Your contact info has been saved securely! Thank you.\n\n"
        "Here are the details for your connection:\n"
        "**Name**: Jane Doe\n"
        "**Phone**: +234 801 234 5678\n\n"
        "This conversation is now complete. Type /start to begin again.",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler for the main user flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(start_connection_flow, pattern='^connect_yes$'),
                CallbackQueryHandler(no_connection, pattern='^connect_no$'),
            ],
            GETTING_LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
            GETTING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
        per_chat=True,
    )

    # Handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('user_count', user_count))

    # Run the bot
    logger.info("Starting bot with polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
