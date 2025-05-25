# Telegram Email Forwarder Bot

A Flask-based Telegram bot to monitor multiple Gmail/Outlook inboxes and forward all incoming emails (including OTPs, verification, etc.) in real-time to Telegram. Supports commands to add new accounts and view emails.

## Features
- `/add <gmail|outlook> <email> <password>`: Add an email account to monitor.
- `/getall`: List all monitored email accounts.
- `/get <email>`: Show last 5 emails for a specific account.
- Real-time notifications for all new emails.

## Deploying for 24/7 Uptime
You can deploy this bot for free on Railway, Replit, or PythonAnywhere. To keep it alive, use [UptimeRobot](https://uptimerobot.com/) to ping the `/webhook` endpoint every 5 minutes.

### 1. Railway
- Sign up at [railway.app](https://railway.app/)
- Create a new Python project and upload the contents of `telegram_email_bot/`.
- Set environment variables: `TELEGRAM_TOKEN`, `ADMIN_CHAT_ID` (your Telegram user ID).
- Set the Flask webserver to listen on 0.0.0.0 and the port from `$PORT`.

### 2. Replit
- Create a new Python repl, upload the files.
- Add environment variables in the Secrets tab.
- Start the Flask app.
- Use [UptimeRobot](https://uptimerobot.com/) to ping your public repl URL `/webhook` endpoint.

### 3. PythonAnywhere
- Create a new web app, upload files.
- Set environment variables in the WSGI file or using the dashboard.
- Point UptimeRobot to your `/webhook` endpoint.

## Setting Telegram Webhook
After deployment, set your webhook:

```
https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook?url=<YOUR_DEPLOYED_URL>/webhook
```

Replace `<YOUR_TELEGRAM_TOKEN>` and `<YOUR_DEPLOYED_URL>` accordingly.

## Requirements
- Python 3.7+
- Flask
- python-telegram-bot==13.15

Install with:
```
pip install -r requirements.txt
```

## Security Note
- Your email credentials are stored in `emails.json` (plaintext). Use only with test or disposable accounts!
- For production, use OAuth2 or a secure vault.

---

Made with ❤️ for monitoring OTPs and verifications in Telegram.
