# Our Two Cents

> A full-stack personal finance tracker for two — powered by Telegram, GPT-4o, Gmail, and a live web dashboard.

![CI](https://img.shields.io/badge/build-passing-brightgreen) ![Python](https://img.shields.io/badge/python-3.13-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Our Two Cents is an automated, AI-powered financial operating system designed specifically for couples. It eliminates the friction of manual expense tracking by seamlessly aggregating transactions from multiple sources—including Gmail receipts, apple pay alerts, and Telegram. Powered by GPT-4o, the system intelligently extracts merchants, amounts, and categories, syncing everything to a live, interactive dashboard. From real-time budget tracking to calculating exact end-of-month settlements, it puts shared finances on autopilot.

## Features

- **Automatic Gmail parsing** — detects financial emails and PDF receipts, extracts amounts and merchants using GPT-4o (supports Hebrew text)
- **Telegram bot** — manual expense entry and real-time AI-generated spending insights every 3 days
- **Card app integration** — receives live transaction webhooks from mobile card apps
- **Interactive dashboard** — filter by month, split type, and payer; view charts, edit transactions inline
- **Budget tracking** — set monthly targets per category, track pacing in real time
- **Settlement calculator** — automatically calculates who owes whom each month
- **Google Sheets export** — export any month's transactions to a Google Sheet with one click
- **AI insights** — GPT-4o-mini analyzes spending patterns and sends alerts via Telegram

## Architecture

```
Gmail / Card App / Telegram
         ↓
  Flask API (PythonAnywhere)
         ↓
  GPT-4o — parse merchant, amount, category
         ↓
  User confirms: Shared or Personal (Telegram inline keyboard)
         ↓
  SQLite Database
         ↓
  Dash Dashboard (Render) — charts, budgets, export
         ↓
  AI Insights (every 3 days) → Telegram notification
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot | pyTelegramBotAPI |
| API | Flask + SQLite |
| AI | GPT-4o, GPT-4o-mini (OpenAI) |
| Email | Gmail API + Google Pub/Sub |
| Dashboard | Dash + Plotly |
| Export | Google Sheets API + gspread |
| Deployment | PythonAnywhere (backend) + Render (frontend) |

## Screenshots

<img width="1851" height="833" alt="image" src="https://github.com/user-attachments/assets/ed16afd8-93ec-43b6-97e5-ffaf4f008c38" />

## Setup

### Prerequisites
- Python 3.11+
- Telegram bot token (via BotFather)
- OpenAI API key
- Google Cloud project with Gmail API, Sheets API, and Pub/Sub enabled

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file with the following variables:

```
TELEGRAM_TOKEN=
MY_CHAT_ID=
OPENAI_API_KEY=
GOOGLE_PROJECT_ID=
SHEETS_SPREADSHEET_ID=
CRON_SECRET=
PAYER_1=YourName
PAYER_2=PartnerName
PAYER_1_EMAIL=your@gmail.com
PAYER_2_EMAIL=partner@gmail.com
```

Run locally:
```bash
python flask_app.py
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
python app.py
```

## Deploy Your Own

This project is fully configurable — anyone can run their own instance for their couple.

1. Fork this repo on GitHub
2. Set up your own PythonAnywhere (backend) and Render (frontend) accounts
3. Set your `.env` variables with your own names, emails, and API keys
4. Run `gmail_setup.py` to authorize Gmail access for both accounts
5. Upload your `service_account.json` to PythonAnywhere
