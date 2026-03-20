import os
import telebot
from flask import Flask, request, jsonify
from telebot import types
from dotenv import load_dotenv

# Note: We are NOT importing database.py or ai_parser.py yet for this test
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Receives the 'tap' from your iPhone.
    Expected JSON: {"text": "...", "payer": "..."}
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON"}), 400

    content = data.get('text', 'Test Transaction')
    payer = data.get('payer', 'Mike')

    # 1. Create the Inline Keyboard (The Buttons)
    markup = types.InlineKeyboardMarkup(row_width=2)

    # callback_data is the hidden string sent back to the server when clicked
    btn_shared = types.InlineKeyboardButton("Shared 🏠",
                                            callback_data="choice_shared")
    btn_personal = types.InlineKeyboardButton("Personal 👤",
                                              callback_data="choice_personal")

    markup.add(btn_shared, btn_personal)

    # 2. Send the message with buttons
    message_text = (
        f"💳 *Transaction Received*\n\n"
        f"👤 *Payer:* {payer}\n"
        f"📝 *Details:* {content}\n\n"
        f"How should we log this?"
    )

    bot.send_message(MY_CHAT_ID, message_text, reply_markup=markup,
                     parse_mode="Markdown")

    return jsonify({"status": "ui_triggered"}), 200


@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    """
    This function runs when you tap 'Shared' or 'Personal' in Telegram.
    """
    # Identify which button was pressed
    if call.data == "choice_shared":
        result_label = "Shared ✅"
    else:
        result_label = "Personal 👤"

    # 3. Update the existing message to show the choice (UX improvement)
    # This replaces the buttons with a confirmation text
    final_text = f"{call.message.text}\n\n📍 *Decision:* {result_label}\n(Not saved to DB yet)"

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=final_text,
        parse_mode="Markdown"
    )

    # 4. Show a small "Toast" notification at the top of Telegram
    bot.answer_callback_query(call.id, f"Selection: {result_label}")


if __name__ == '__main__':
    app.run(port=8000, debug=True)
