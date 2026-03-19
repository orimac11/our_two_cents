import sys
import os
import json
from dotenv import load_dotenv
import telebot
from flask import Flask, request, jsonify
from telebot import types


# --- 1. CONFIGURATION & SETUP ---

def setup_pythonanywhere_path():
    """Fixes the module import path for PythonAnywhere environment."""
    server_path = "/home/michaelketash/.local/lib/python3.13/site-packages"
    if os.path.exists(server_path) and server_path not in sys.path:
        sys.path.insert(0, server_path)


setup_pythonanywhere_path()
load_dotenv()

# Environment Variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

# Initialize Global Objects
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)


# --- 2. TELEGRAM HELPER FUNCTIONS ---

def create_classification_keyboard(raw_text):
    """
    Creates the inline buttons for 'Shared' and 'Personal' options.
    Trims the text to fit Telegram's callback_data limit (64 bytes).
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    callback_payload = raw_text[:30]  # Keep payload short

    btn_shared = types.InlineKeyboardButton(
        "🏠 Shared",
        callback_data=f"set_shared|{callback_payload}"
    )
    btn_personal = types.InlineKeyboardButton(
        "👤 Personal",
        callback_data=f"set_personal|{callback_payload}"
    )

    markup.add(btn_shared, btn_personal)
    return markup


def send_expense_notification(chat_id, expense_text):
    """Formats and sends the initial expense notification to Telegram."""
    keyboard = create_classification_keyboard(expense_text)
    message_body = (
        f"💰 *New Expense Detected:*\n"
        f"`{expense_text}`\n\n"
        f"How should we classify this?"
    )
    bot.send_message(
        chat_id,
        message_body,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


def handle_classification_update(call):
    """Updates the Telegram message UI based on the user's button click."""
    action, expense_name = call.data.split('|')

    if action == "set_shared":
        status_text = f"✅ *Updated as Shared:* {expense_name}\n(Recorded in Shared Report)"
    else:
        status_text = f"❌ *Classified as Personal:* {expense_name}\n(Personal Expense Only)"

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=status_text,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id, "Selection Saved!")


# --- 3. FLASK ROUTES (ENDPOINTS) ---

@app.route('/')
def health_check():
    return "🚀 Finance Agent Service: Operational"


@app.route('/webhook', methods=['POST'])
def handle_incoming_sms():
    """Endpoint for iOS Shortcuts to post raw SMS data."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Payload missing 'text' field"}), 400

        raw_sms_text = data['text']
        print(f"Processing SMS: {raw_sms_text}")

        # Trigger the Telegram flow
        send_expense_notification(MY_CHAT_ID, raw_sms_text)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Webhook Exception: {e}")
        return jsonify({"error": str(e)}), 500


# --- 4. TELEGRAM CALLBACK HANDLERS ---

@bot.callback_query_handler(func=lambda call: True)
def on_button_click(call):
    """Entry point for all button interactions in Telegram."""
    handle_classification_update(call)


# --- 5. EXECUTION ---

if __name__ == '__main__':
    # Local development server
    app.run(port=8000, debug=True)