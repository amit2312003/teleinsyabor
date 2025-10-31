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
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8103775533:AAGuXitKiY9USeGPlk792TPjDH7F7rNoFjg")
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
ADMIN_USER_ID = 5204957178

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL_ENTRY = range(1)
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
    service = Service('/usr/bin/chromedriver')  # For local, update to your path if needed
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
        driver.find_element
