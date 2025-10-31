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
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import logging

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8103775533:AAGuXitKiY9USeGPlk792TPjDH7F7rNoFjg")
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
ADMIN_USER_ID = 5204957178

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL_ENTRY = 1
admin_email = {}
admin_pass = {}

def fetch_proxies_spys_one():
    proxy_url = "https://spys.me/proxy.txt"
    try:
        resp = requests.get(proxy_url, timeout=10)
        proxies = []
        if resp.status_code == 200:
            lines = resp.text.splitlines()
            for line in lines:
                if line and not line.startswith("#") and ":" in line:
                    proxies.append(line.strip())
        logger.info(f"Fetched {len(proxies)} proxies from spys.one.")
        return proxies
    except Exception as e:
        logger.error(f"Error fetching proxies from Spys.one: {e}")
        return []

def generate_random_name():
    first_names = ["John", "Emma", "Michael", "Sophia", "William", "Olivia", "James", "Ava", "Lucas", "Isabella"]
    last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_username():
    prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

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

def get_available_username(driver, wait, full_name, password, email):
    for _ in range(10):
        username = generate_username()
        driver.get(INSTAGRAM_SIGNUP_URL)
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))).clear()
        driver.find_element(By.NAME, "emailOrPhone").send_keys(email)
        driver.find_element(By.NAME, "fullName").clear()
        driver.find_element(By.NAME, "fullName").send_keys(full_name)
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(2)
        error_divs = driver.find_elements(By.XPATH, "//div[contains(text(),'Another account is using')]")
        if not error_divs:
            logger.info(f"Available username: {username}")
            return username
        logger.info(f"Username {username} not available, retrying...")
    raise Exception("Unable to find available username after 10 tries!")

def switch_to_creator_account(driver, wait):
    try:
        logger.info("Switching to professional account...")
        driver.get("https://www.instagram.com/accounts/edit/")
        time.sleep(5)
        try:
            switch_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Switch to professional account')]")))
            switch_button.click()
            time.sleep(3)
        except:
            driver.get("https://www.instagram.com/accounts/convert_to_professional_account/")
            time.sleep(3)
        try:
            creator_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Creator')]//ancestor::button")))
            creator_button.click()
            time.sleep(2)
            next_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Next')]")
            next_btn.click()
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error selecting creator: {e}")
        try:
            personal_category = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Personal') or contains(text(),'Blog')]//ancestor::button")))
            personal_category.click()
            time.sleep(2)
            done_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Done') or contains(text(),'Next')]")
            done_btn.click()
            time.sleep(3)
            logger.info("✅ Successfully switched to creator account")
        except Exception as e:
            logger.error(f"Error selecting category: {e}")
        for _ in range(3):
            try:
                skip_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Skip') or contains(text(),'Not Now')]")
                skip_btn.click()
                time.sleep(2)
            except:
                break
        return True
    except Exception as e:
        logger.error(f"Error switching to professional: {e}")
        return False

def create_instagram_account(email, password):
    driver = None
    try:
        proxies_list = fetch_proxies_spys_one()
        proxy = random.choice(proxies_list) if proxies_list else None
        full_name = generate_random_name()
        driver = setup_driver(proxy)
        wait = WebDriverWait(driver, 15)
        username = get_available_username(driver, wait, full_name, password, email)
        driver.get(INSTAGRAM_SIGNUP_URL)
        wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))).clear()
        driver.find_element(By.NAME, "emailOrPhone").send_keys(email)
        driver.find_element(By.NAME, "fullName").clear()
        driver.find_element(By.NAME, "fullName").send_keys(full_name)
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        logger.info("Submitted signup form")
        time.sleep(5)
        try:
            month_select = driver.find_element(By.XPATH, "//select[@title='Month:']")
            month_select.send_keys("January")
            day_select = driver.find_element(By.XPATH, "//select[@title='Day:']")
            day_select.send_keys("15")
            year_select = driver.find_element(By.XPATH, "//select[@title='Year:']")
            year_select.send_keys("1995")
            next_button = driver.find_element(By.XPATH, "//button[contains(text(),'Next')]")
            next_button.click()
            time.sleep(3)
        except Exception:
            pass
        driver.quit()
        return (
            f"✅ Instagram Account Created (check your email manually for OTP)!\n\n"
            f"📧 Email: {email}\n"
            f"👤 Username: {username}\n"
            f"🔐 Password: {password}\n"
            f"👥 Name: {full_name}\n"
            f"💼 Type: Creator (Manual, OTP required)\n"
            f"🧑‍💻 Proxy Used: {proxy}\n"
        )
    except Exception as e:
        if driver:
            driver.quit()
        logger.error(f"Error creating account: {e}")
        return f"❌ Error: {str(e)}"

def restrict_admin(func):
    async def wrapper(update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("⛔ Only admin can run this command.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

async def start(update, context):
    await update.message.reply_text(
        "🤖 Instagram Account Creator Bot\n\n"
        "/addmail - Enter your email for registration (admin only)\n"
        "/addpass yourpassword - Enter your password for registration (admin only)\n"
        "⚠️ After submitting, check your email for OTP and finish registration manually."
    )

@restrict_admin
async def addmail(update, context):
    await update.message.reply_text("✉️ Please send the email address to use for Instagram registration.")
    return EMAIL_ENTRY

@restrict_admin
async def addmail_entry(update, context):
    admin_email[update.effective_user.id] = update.message.text.strip()
    await update.message.reply_text("🔐 Now send the password to use via /addpass yourpassword")
    return ConversationHandler.END

@restrict_admin
async def addpass(update, context):
    parts = update.message.text.split(maxsplit=1)
    if len(parts) != 2:
        await update.message.reply_text("Usage: /addpass yourpassword")
        return
    admin_pass[update.effective_user.id] = parts[1]
    email = admin_email.get(update.effective_user.id)
    password = admin_pass.get(update.effective_user.id)
    if not email:
        await update.message.reply_text("First set email with /addmail.")
        return
    await update.message.reply_text("🚀 Creating Instagram account...")
    result = create_instagram_account(email, password)
    await update.message.reply_text(result)
    await update.message.reply_text("⚠️ Now check your email for OTP, and finish registration manually!")

async def cancel(update, context):
    await update.message.reply_text("Manual registration cancelled.")
    return ConversationHandler.END

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addmail', addmail)],
        states={
            EMAIL_ENTRY: [MessageHandler(filters.TEXT & (~filters.COMMAND), addmail_entry)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('addpass', addpass))
    application.add_error_handler(error_handler)
    application.run_polling()
    logger.info("✅ Bot is running and connected to Telegram!")

if __name__ == "__main__":
    main()
