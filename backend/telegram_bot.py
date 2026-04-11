"""
telegram_bot.py
===============

Telegram bot UI and message handlers for the finance bot.

Provides a shared/personal split decision UI sent after each detected transaction,
a ``/add`` command for manual expense entry, and a callback handler that saves
the confirmed expense to the database.
"""

import os
import re
from telebot import types
from ai_parser import parser_service
from database_manager import add_pending_expense, confirm_expense_split

PAYER_1 = os.getenv('PAYER_1', 'Michael')
PAYER_2 = os.getenv('PAYER_2', 'Ori')


def send_transaction_ui(bot, chat_id: str | int, merchant: str, amount: float,
                        category: str, payer: str, expense_id: int | None = None) -> None:
    """Send an inline keyboard message asking the user to choose a split type.

    Encodes the expense DB row ID into the callback payload so the button handler
    can update the existing pending row rather than inserting a duplicate.

    :param bot: The ``telebot.TeleBot`` instance to send the message with.
    :param chat_id: Telegram chat ID to send the message to.
    :param merchant: Merchant name extracted by the AI parser.
    :param amount: Transaction amount in ILS.
    :param category: Expense category assigned by the AI parser.
    :param payer: Name of the person who made the transaction.
    :param expense_id: DB row ID of the pending expense to confirm.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    id_part = str(expense_id) if expense_id is not None else "0"
    cb_shared = f"shrd|{id_part}"
    cb_priv = f"priv|{id_part}"

    print(f"[DEBUG] Callback Length: {len(cb_shared.encode('utf-8'))} bytes")

    markup.add(
        types.InlineKeyboardButton("Shared 🏠", callback_data=cb_shared),
        types.InlineKeyboardButton("Personal 👤", callback_data=cb_priv)
    )
    message_text = (
        f"💳 *New Transaction*\n\n"
        f"🏪 *Store:* `{merchant}`\n"
        f"💰 *Amount:* `₪{amount}`\n"
        f"📂 *Category:* `{category}`\n"
        f"👤 *Payer:* `{payer}`\n\n"
        f"*Split?*"
    )
    bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode="Markdown")


def register_handlers(bot) -> None:
    """Register all Telegram message and callback handlers on the bot instance.

    :param bot: The ``telebot.TeleBot`` instance to register handlers on.
    """

    @bot.message_handler(commands=['add'])
    def handle_manual_add(message):
        """Handle the ``/add`` command for manual expense entry.

        Parses the text after ``/add`` through the AI parser and sends
        the split decision UI if a valid amount is detected.
        """
        raw_text = message.text.replace('/add', '').strip()

        if not raw_text:
            bot.reply_to(message, "❌ Please provide details. Ex: `/add 50 Aroma`")
            return

        enriched = parser_service.parse(raw_text)
        print(f"[DEBUG] Parser result for '{raw_text}': {enriched}")

        # Fallback: if AI missed the amount, try extracting the first number from raw text
        if enriched['amount'] <= 0:
            match = re.search(r'\d+(?:[.,]\d+)?', raw_text)
            if match:
                fallback_amount = float(match.group().replace(',', '.'))
                print(f"[DEBUG] AI returned 0, using regex fallback amount: {fallback_amount}")
                enriched['amount'] = fallback_amount

        if enriched['amount'] <= 0:
            bot.reply_to(
                message,
                "⚠️ *No amount detected.*\n"
                "Please include a price so I can log it correctly.\n"
                "Ex: `/add 45 Super-Pharm`",
                parse_mode="Markdown"
            )
            return

        expense_id = add_pending_expense(
            merchant=enriched['merchant'],
            amount=enriched['amount'],
            payer=message.from_user.first_name,
            category=enriched['category'],
        )
        send_transaction_ui(
            bot=bot,
            chat_id=message.chat.id,
            merchant=enriched['merchant'],
            amount=enriched['amount'],
            category=enriched['category'],
            payer=message.from_user.first_name,
            expense_id=expense_id,
        )

    @bot.callback_query_handler(func=lambda call: True)
    def handle_ui_decision(call):
        """Handle the shared/personal button press from the transaction UI.

        Parses the ``|``-delimited callback payload containing the expense row ID,
        updates the pending expense's split type, and edits the original message.
        """
        try:
            print(f"[DEBUG] Button Pressed! Raw Data received: {call.data}")

            data_parts = call.data.split('|')
            if len(data_parts) < 2:
                print(f"[ERROR] Callback data is incomplete: {call.data}")
                return

            action, expense_id_str = data_parts[0], data_parts[1]
            db_split = "shared" if action == "shrd" else "personal"
            expense_id = int(expense_id_str)

            print(f"[DEBUG] Confirming expense #{expense_id} as {db_split}")

            success = confirm_expense_split(expense_id, db_split)

            if success:
                print(f"[SUCCESS] Expense #{expense_id} confirmed as {db_split}.")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ *Logged* | {db_split.capitalize()}",
                    parse_mode="Markdown"
                )
            else:
                print(f"[ERROR] confirm_expense_split returned False for id={expense_id}.")

            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"[CRITICAL ERROR] In handle_ui_decision: {str(e)}")
            bot.answer_callback_query(call.id, "System Error. Check Logs.")