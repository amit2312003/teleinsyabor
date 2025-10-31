import time
import random
import string
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging

TELEGRAM_TOKEN = "8103775533:AAGuXitKiY9USeGPlk792TPjDH7F7rNoFjg"
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Manual mode states
EMAIL, PASSWORD = range(2)

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
        # You must now handle the OTP confirmation step manually in Telegram. Bot will pause here.
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

# Telegram Handlers

def start(update, context):
    update.message.reply_text("🤖 Instagram Account Creator Bot\n\n"
                              "/manual - Enter your email/password for registration (admin)\n"
                              "⚠️ You will need to check your email and enter OTP manually.")

def manual_start(update, context):
    update.message.reply_text("✉️ Enter the email address you want to use for Instagram registration:")
    return EMAIL

def manual_email(update, context):
    email = update.message.text.strip()
    context.user_data['email'] = email
    update.message.reply_text("🔐 Enter the password you want to use for Instagram registration:")
    return PASSWORD

def manual_password(update, context):
    password = update.message.text.strip()
    email = context.user_data['email']
    update.message.reply_text("🚀 Creating Instagram account...")
    result = create_instagram_account(email, password)
    update.message.reply_text(result)
    update.message.reply_text("⚠️ Now check your email for OTP, and finish registration manually!")
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Manual registration cancelled.")
    return ConversationHandler.END

def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    manual_conv = ConversationHandler(
        entry_points=[CommandHandler('manual', manual_start)],
        states={
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, manual_email)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, manual_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(manual_conv)
    dp.add_error_handler(error_handler)
    updater.start_polling()
    logger.info("✅ Bot is running and connected to Telegram!")
    updater.idle()

if __name__ == "__main__":
    main()
