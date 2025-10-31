import time
import random
import string
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram.ext import Updater, CommandHandler
import logging

TELEGRAM_TOKEN = "8103775533:AAGuXitKiY9USeGPlk792TPjDH7F7rNoFjg"
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=12))

# Mail.tm API functions
def create_mailtm_account():
    domains = requests.get("https://api.mail.tm/domains").json()["hydra:member"]
    domain = random.choice(domains)["domain"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    email = f"{username}@{domain}"
    resp = requests.post("https://api.mail.tm/accounts", json={"address": email, "password": password})
    if resp.status_code not in [200, 201]:
        raise Exception("Couldn't create mail.tm account")
    resp = requests.post("https://api.mail.tm/token", json={"address": email, "password": password})
    token = resp.json()["token"]
    return email, password, token

def get_mailtm_otp(token, sender="instagram"):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(30):
        r = requests.get("https://api.mail.tm/messages", headers=headers)
        mails = r.json().get("hydra:member", [])
        for mail in mails:
            subject = mail.get("subject", "").lower()
            if sender in subject:
                msgid = mail["id"]
                msg = requests.get(f"https://api.mail.tm/messages/{msgid}", headers=headers).json()
                text = msg.get("text", "")
                m = re.search(r"\b(\d{6})\b", text)
                if m:
                    return m.group(1)
        time.sleep(5)
    return None

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
    # Use pre-installed chromedriver from Dockerfile (make sure it's in your Dockerfile as described in previous answers)
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
            switch_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(),'Switch to professional account')]")
            ))
            switch_button.click()
            time.sleep(3)
        except:
            driver.get("https://www.instagram.com/accounts/convert_to_professional_account/")
            time.sleep(3)
        try:
            creator_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(),'Creator')]//ancestor::button")
            ))
            creator_button.click()
            time.sleep(2)
            next_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Next')]")
            next_btn.click()
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error selecting creator: {e}")
        try:
            personal_category = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(),'Personal') or contains(text(),'Blog')]//ancestor::button")
            ))
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

def create_instagram_account():
    driver = None
    try:
        proxies_list = fetch_proxies_spys_one()
        proxy = random.choice(proxies_list) if proxies_list else None

        # Mail.tm email
        email, mailtmpass, mailtmtoken = create_mailtm_account()
        full_name = generate_random_name()
        password = generate_password()
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
        # birthday
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
        otp = get_mailtm_otp(mailtmtoken)
        if not otp:
            driver.quit()
            return f"❌ Could not get OTP from mail.tm for: {email}"
        try:
            otp_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            otp_input.clear()
            otp_input.send_keys(otp)
            time.sleep(1)
            confirm_button = driver.find_element(By.XPATH, "//button[contains(text(),'Next') or contains(text(),'Confirm')]")
            confirm_button.click()
            logger.info("OTP submitted successfully")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error submitting OTP: {e}")
            driver.quit()
            return f"❌ Failed to submit OTP\n📧 Email: {email}\n👤 Username: {username}\n🔐 Password: {password}"
        switch_to_creator_account(driver, wait)
        driver.quit()
        return (
            f"✅ Instagram Account Created Successfully!\n\n"
            f"📧 Email: {email}\n"
            f"👤 Username: {username}\n"
            f"🔐 Password: {password}\n"
            f"👥 Name: {full_name}\n"
            f"💼 Type: Creator (Personal)\n"
            f"🧑‍💻 Proxy Used: {proxy}\n"
            f"📨 OTP Source: mail.tm"
        )
    except Exception as e:
        if driver:
            driver.quit()
        logger.error(f"Error creating account: {e}")
        return f"❌ Error: {str(e)}"

def start(update, context):
    update.message.reply_text(
        "🤖 Instagram Account Creator Bot\n\n"
        "/create - Auto-create Instagram account using mail.tm and live proxies\n"
        "⚠️ Educational purposes only"
    )

def help_command(update, context):
    update.message.reply_text(
        "📖 How to use:\n"
        "1. Send /create\n"
        "2. Bot will use a random IP (proxy), register email, and fetch everything for you\n"
        "3. Wait for account details!"
    )

def create_account_command(update, context):
    update.message.reply_text("🔄 Creating Instagram account with proxy (IP Rotate)...\n⏳ Please wait 2-5 minutes...")
    try:
        result = create_instagram_account()
        update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Error in create command: {e}")
        update.message.reply_text(f"❌ An error occurred: {str(e)}")

def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    logger.info("Starting Instagram Creator Bot...")
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("create", create_account_command))
    dp.add_error_handler(error_handler)
    updater.start_polling()
    logger.info("✅ Bot is running and connected to Telegram!")
    updater.idle()

if __name__ == "__main__":
    main()
