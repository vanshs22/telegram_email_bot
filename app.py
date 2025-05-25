import os
import threading
import time
import json
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler
import imaplib
import email

# --- Configuration ---
TELEGRAM_TOKEN = "8112289580:AAGS2GPHtWvnPyRPWZzpHl2gpBPIKIL0cyw"
ADMIN_CHAT_ID = "1863750440"  # Optionally restrict access
EMAILS_FILE = 'emails.json'

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# --- Persistence ---
def load_emails():
    if not os.path.exists(EMAILS_FILE):
        return {}
    with open(EMAILS_FILE, 'r') as f:
        return json.load(f)

def save_emails(emails):
    with open(EMAILS_FILE, 'w') as f:
        json.dump(emails, f)

# --- Email Polling ---
class EmailChecker(threading.Thread):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id
        self.running = True

    def run(self):
        while self.running:
            emails = load_emails()
            for email_addr, info in emails.items():
                try:
                    self.check_email(email_addr, info)
                except Exception as e:
                    print(f'Error checking {email_addr}:', e)
            time.sleep(15)  # Poll every 15 seconds

    def check_email(self, email_addr, info):
        password = info['password']
        provider = info['provider']
        imap_host = 'imap.gmail.com' if provider == 'gmail' else 'outlook.office365.com'
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(email_addr, password)
        mail.select('inbox')
        result, data = mail.search(None, 'UNSEEN')
        if result != 'OK':
            return
        ids = data[0].split()
        for num in ids:
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result != 'OK':
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg['subject']
            from_ = msg['from']
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')
            text = f'📧 New mail for {email_addr}\nFrom: {from_}\nSubject: {subject}\nBody:\n{body[:500]}'
            self.bot.send_message(chat_id=self.chat_id, text=text)
        mail.logout()

    def stop(self):
        self.running = False

# --- Telegram Handlers ---
def start(update, context):
    update.message.reply_text('Welcome! Use /add to add an email, /getall to list emails, /get <email> to see emails.')

def add_email(update, context):
    args = context.args
    if len(args) != 3:
        update.message.reply_text('Usage: /add <gmail|outlook> <email> <password>')
        return
    provider, email_addr, password = args
    if provider not in ['gmail', 'outlook']:
        update.message.reply_text('Provider must be gmail or outlook.')
        return
    emails = load_emails()
    emails[email_addr] = {'password': password, 'provider': provider}
    save_emails(emails)
    update.message.reply_text(f'Added {email_addr} ({provider})!')

def getall(update, context):
    emails = load_emails()
    if not emails:
        update.message.reply_text('No emails added yet.')
        return
    text = '\n'.join([f'{k} ({v["provider"]})' for k,v in emails.items()])
    update.message.reply_text('Monitored emails:\n' + text)

def get_email(update, context):
    args = context.args
    if not args:
        update.message.reply_text('Usage: /get <email>')
        return
    email_addr = args[0]
    emails = load_emails()
    if email_addr not in emails:
        update.message.reply_text('Email not found.')
        return
    info = emails[email_addr]
    provider = info['provider']
    password = info['password']
    imap_host = 'imap.gmail.com' if provider == 'gmail' else 'outlook.office365.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(email_addr, password)
        mail.select('inbox')
        result, data = mail.search(None, 'ALL')
        if result != 'OK':
            update.message.reply_text('Failed to fetch emails.')
            return
        ids = data[0].split()[-5:]
        msgs = []
        for num in ids:
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result != 'OK':
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg['subject']
            from_ = msg['from']
            msgs.append(f'From: {from_}\nSubject: {subject}')
        mail.logout()
        if msgs:
            update.message.reply_text('\n---\n'.join(msgs))
        else:
            update.message.reply_text('No emails found.')
    except Exception as e:
        update.message.reply_text(f'Error: {e}')

def main():
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('add', add_email))
    dispatcher.add_handler(CommandHandler('getall', getall))
    dispatcher.add_handler(CommandHandler('get', get_email))
    # Start email checker
    chat_id = ADMIN_CHAT_ID or 'YOUR_TELEGRAM_CHAT_ID'
    checker = EmailChecker(bot, chat_id)
    checker.daemon = True
    checker.start()
    return checker

checker = None

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

checker = main()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
