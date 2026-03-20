import os
import telebot
from flask import Flask, request, jsonify
from telebot import types
from dotenv import load_dotenv

# --- 1. SETUP & CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

# Get credentials from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

# Initialize Bot and Flask app
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)


# --- 2. WEBHOOK ROUTE (RECEIVER) ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Receives the structured data from the iOS Shortcut.
    Expected JSON: {"merchant": "...", "amount": "...", "payer": "..."}
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400

    # Extract data from the Shortcut request
    merchant = data.get('merchant', 'Unknown Store')
    amount = data.get('amount', '0.0')
    payer = data.get('payer', 'Michael')

    # Create the Inline Keyboard (The Buttons)
    markup = types.InlineKeyboardMarkup(row_width=2)

    # CRITICAL: Use a structured string for callback_data (max 64 bytes)
    # Format: action|merchant|amount
    cb_shared = f"btn_shrd|{merchant[:20]}|{amount}"
    cb_private = f"btn_priv|{merchant[:20]}|{amount}"

    btn_shared = types.InlineKeyboardButton("Shared 🏠", callback_data=cb_shared)
    btn_personal = types.InlineKeyboardButton("Personal 👤",
                                              callback_data=cb_private)

    markup.add(btn_shared, btn_personal)

    # Format the message text with Markdown
    message_text = (
        f"💳 *New Transaction Detected*\n\n"
        f"🏪 *Store:* `{merchant}`\n"
        f"💰 *Amount:* `₪{amount}`\n"
        f"👤 *Payer:* `{payer}`\n\n"
        f"Should we split this expense?"
    )

    # Send message to the Telegram group/chat
    bot.send_message(MY_CHAT_ID, message_text, reply_markup=markup,
                     parse_mode="Markdown")

    return jsonify({"status": "success", "received": merchant}), 200


# --- 3. CALLBACK HANDLER (INTERACTION) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    """
    Triggers when a user clicks 'Shared' or 'Personal'.
    Unpacks the merchant and amount from the callback_data.
    """
    try:
        # Unpack the data string: "action|merchant|amount"
        parts = call.data.split('|')
        action = parts[0]  # "btn_shrd" or "btn_priv"
        merchant = parts[1]
        amount = parts[2]

        # Determine the decision label
        if action == "btn_shrd":
            result_label = "Shared 🏠"
        else:
            result_label = "Personal 👤"

        # Update the UI: Reconstruct the message to confirm the choice
        final_text = (
            f"✅ *Transaction Finalized*\n\n"
            f"🏪 *Store:* {merchant}\n"
            f"💰 *Amount:* ₪{amount}\n\n"
            f"📍 *Decision:* {result_label}\n"
            f"_(Not saved to DB yet)_"
        )

        # Edit the original message to remove the buttons and show the result
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=final_text,
            parse_mode="Markdown"
        )

        # Answer the callback to remove the "loading" spinner on the button
        bot.answer_callback_query(call.id, f"Logged as {result_label}")

    except Exception as e:
        print(f"Error in callback: {e}")
        bot.answer_callback_query(call.id, "Error processing selection.")

# 3. The Telegram Route (The Listening Ear)
@app.route('/telegram', methods=['POST'])
def telegram_input():
    """
    Matches the webhook URL we will give to Telegram.
    Catches everything typed in the bot's chat.
    """
    data = request.json
    # CRITICAL: We must reply with a 200 OK immediately.
    # If we don't, Telegram assumes the server is dead and will retry sending the message 50 times.
    return jsonify({"status": "ok"}), 200


@bot.message_handler(commands=['add'])
def handle_manual_add(message):
    """
    Fires when you type: /add 50 Aroma
    """
    # 1. Extract the text after the command
    content = message.text.replace('/add', '').strip()

    if not content:
        bot.reply_to(message,
                     "❌ Please provide details. Example: /add 50 Aroma")
        return

    # 2. Create buttons using the EXACT SAME 'Pipe' format: action|merchant|amount
    # We put 'Manual' in the amount slot so the handler knows how to display it.
    markup = types.InlineKeyboardMarkup(row_width=2)

    cb_shared = f"btn_shrd|{content[:20]}|Manual"
    cb_personal = f"btn_priv|{content[:20]}|Manual"

    # Note: Changed 'callback_id' to 'callback_data'
    btn_shared = types.InlineKeyboardButton("Shared 🏠", callback_data=cb_shared)
    btn_personal = types.InlineKeyboardButton("Personal 👤",
                                              callback_data=cb_personal)

    markup.add(btn_shared, btn_personal)

    # 3. Send the message
    message_text = (
        f"📝 *Manual Entry Received*\n\n"
        f"👤 *Payer:* {message.from_user.first_name}\n"
        f"📖 *Details:* {content}\n\n"
        f"How should we log this?"
    )

    bot.send_message(message.chat.id, message_text, reply_markup=markup,
                     parse_mode="Markdown")
# --- 4. EXECUTION ---
if __name__ == '__main__':
    # Local development server (port 8000)
    app.run(port=8000, debug=True)