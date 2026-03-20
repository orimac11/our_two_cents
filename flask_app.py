from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
# These should be set in your .env file on PythonAnywhere
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_GROUP_CHAT_ID = os.getenv('MY_CHAT_ID')

def send_to_telegram(payer, content):
    """Sends a formatted debug message to verify the 'Plumbing'."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message_text = (
        f"🔗 <b>Webhook Triggered!</b>\n\n"
        f"👤 <b>Payer:</b> {payer}\n"
        f"📝 <b>Input:</b> {content}\n\n"
        f"<i>Status: Server is listening on /webhook</i>"
    )

    payload = {
        "chat_id": TELEGRAM_GROUP_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram API Error: {e}")

# 2. The Synchronized Route
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Matches your iOS Shortcut URL ending in /webhook.
    Expects: {"text": "...", "payer": "..."}
    """
    data = request.json

    if not data:
        print("Error: Received request with no JSON body")
        return jsonify({"error": "No JSON received"}), 400

    # Extracting the new fields
    content = data.get('text', 'No text provided')
    payer = data.get('payer', 'Unknown')

    print(f"Success: Received data from {payer}")

    # Send the verification message
    send_to_telegram(payer, content)

    return jsonify({"status": "connected", "received": content}), 200

# 3. Health Check for Browser Testing
@app.route('/')
def index():
    return "🚀 Server is live and listening on /webhook"

if __name__ == '__main__':
    app.run(port=8000, debug=True)