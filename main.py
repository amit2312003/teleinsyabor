import os
import time
import random
import string
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "your-telegram-token-here")
ADMIN_USER_ID = 5204957178
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
EMAIL_STEP, PASS_STEP, OTP_STEP = range(3)
admin_email = {}
admin_pass = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver(proxy=None):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')
        logger.info(f"Using proxy: {proxy}")
    service = Service('/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=options)

def generate_random_name():
    first_names = ["John", "Emma", "Michael", "Sophia", "William", "Olivia", "James", "Ava", "Lucas", "Isabella"]
    last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_username():
    prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def robust_instagram_signup(email, password):
    full_name = generate_random_name()
    username = generate_username()
    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 30)
        driver.get(INSTAGRAM_SIGNUP_URL)
        wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))).send_keys(email)
        driver.find_element(By.NAME, "fullName").send_keys(full_name)
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(2)
        # Click "Sign Up"
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        logger.info("Sign Up form submitted")
        # Wait for birthdate page
        wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
        driver.find_element(By.XPATH, "//select[@title='Month:']").send_keys("January")
        driver.find_element(By.XPATH, "//select[@title='Day:']").send_keys("10")
        driver.find_element(By.XPATH, "//select[@title='Year:']").send_keys("2001")
        driver.find_element(By.XPATH, "//button[contains(text(),'Next')]").click()
        logger.info("Birthdate submitted")
        # Wait for OTP mail trigger
        time.sleep(18) # Change to 30 if on slow connection
        driver.quit()
        # Return details
        return full_name, username
    except Exception as e:
        logger.error(f"Error: {e}")
        if driver:
            driver.quit()
        return None, None

def restrict_admin(func):
    async def wrapper(update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("⛔ Only admin can run this command.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

async def start(update, context):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Only admin can use this bot.")
        return ConversationHandler.END
    buttons = [
        [InlineKeyboardButton("➕ Add Email", callback_data="addmail")],
    ]
    await update.message.reply_text("Welcome! Tap to begin:", reply_markup=InlineKeyboardMarkup(buttons))

async def addmail_btn(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✉️ Enter your email for IG signup:")
    return EMAIL_STEP

async def save_email(update, context):
    admin_email[ADMIN_USER_ID] = update.message.text.strip()
    buttons = [[InlineKeyboardButton("🔐 Add Password", callback_data="addpass")]]
    await update.message.reply_text("Email saved.", reply_markup=InlineKeyboardMarkup(buttons))
    return PASS_STEP

async def addpass_btn(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Enter your IG password (will be used for automation):")
    return PASS_STEP

async def save_pass(update, context):
    admin_pass[ADMIN_USER_ID] = update.message.text.strip()
    email = admin_email.get(ADMIN_USER_ID, "")
    password = admin_pass.get(ADMIN_USER_ID, "")
    await update.message.reply_text(
        f"`📧 Email: {email}`\n`🔐 Password: {password}`",
        parse_mode="Markdown"
    )
    await update.message.reply_text("Submitting registration. Wait for OTP to arrive in your inbox...", parse_mode="Markdown")
    full_name, username = robust_instagram_signup(email, password)
    if full_name is None:
        await update.message.reply_text("❌ Failed to create IG account. Check logs and try again.")
        return ConversationHandler.END
    await update.message.reply_text("When you receive your IG OTP by email, enter it here:")
    return OTP_STEP

async def save_otp(update, context):
    otp = update.message.text.strip()
    await update.message.reply_text(f"`🔑 Your OTP is: {otp}`\nComplete registration in IG browser.", parse_mode="Markdown")
    await update.message.reply_text("✅ Flow complete. Check your IG account.")
    return ConversationHandler.END

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(addmail_btn, pattern="addmail"),
        ],
        states={
            EMAIL_STEP: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_email)],
            PASS_STEP: [
                CallbackQueryHandler(addpass_btn, pattern="addpass"),
                MessageHandler(filters.TEXT & (~filters.COMMAND), save_pass),
            ],
            OTP_STEP: [MessageHandler(filters.TEXT & (~filters.COMMAND), save_otp)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling()
    logger.info("✅ Bot running!")

if __name__ == "__main__":
    main()
