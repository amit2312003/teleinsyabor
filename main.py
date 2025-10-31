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
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

# ========== CONFIGURATION ==========
TELEGRAM_TOKEN = "8103775533:AAGuXitKiY9USeGPlk792TPjDH7F7rNoFjg"
INSTAGRAM_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== HELPER FUNCTIONS ==========

def generate_random_name():
    """Generate random full name"""
    first_names = ["John", "Emma", "Michael", "Sophia", "William", "Olivia", "James", "Ava"]
    last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Moore", "Taylor", "Anderson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_username():
    """Generate random username"""
    prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def generate_password():
    """Generate strong random password"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=12))

def get_temp_mail():
    """Fetch temporary email using temp-mail.org API"""
    try:
        # Generate random email using temp-mail.org domains
        domains_response = requests.get("https://api.internal.temp-mail.org/request/domains/")
        if domains_response.status_code == 200:
            domains = domains_response.json()
            if domains:
                username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                email = f"{username}{random.choice(domains)}"
                logger.info(f"Generated temp email: {email}")
                return email
    except Exception as e:
        logger.error(f"Error getting temp mail: {e}")
    return None

def get_otp_from_temp_mail(email):
    """Poll temp mail inbox for Instagram OTP"""
    try:
        md5_email = requests.utils.quote(email)
        inbox_url = f"https://api.internal.temp-mail.org/request/mail/id/{md5_email}/"
        
        logger.info("Waiting for OTP email...")
        for attempt in range(30):  # Try for 2.5 minutes
            try:
                response = requests.get(inbox_url)
                if response.status_code == 200:
                    mails = response.json()
                    if mails:
                        for mail in mails:
                            subject = mail.get('mail_subject', '')
                            text = mail.get('mail_text_only', '') or mail.get('mail_text', '')
                            
                            if "instagram" in subject.lower() or "instagram" in text.lower():
                                # Find 6-digit OTP code
                                otp_match = re.search(r'\b(\d{6})\b', text)
                                if otp_match:
                                    otp = otp_match.group(1)
                                    logger.info(f"OTP found: {otp}")
                                    return otp
            except Exception as e:
                logger.error(f"Error checking inbox: {e}")
            
            time.sleep(5)
        
        logger.error("OTP not received within timeout")
    except Exception as e:
        logger.error(f"Error fetching OTP: {e}")
    
    return None

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def create_instagram_account():
    """Main function to create Instagram account"""
    driver = None
    try:
        # Generate account details
        email = get_temp_mail()
        if not email:
            return "❌ Failed to generate temporary email"
        
        full_name = generate_random_name()
        username = generate_username()
        password = generate_password()
        
        logger.info(f"Creating account with email: {email}")
        
        # Setup Selenium driver
        driver = setup_driver()
        driver.get(INSTAGRAM_SIGNUP_URL)
        time.sleep(3)
        
        # Fill signup form
        wait = WebDriverWait(driver, 15)
        
        # Enter email
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(1)
        
        # Enter full name
        name_input = driver.find_element(By.NAME, "fullName")
        name_input.clear()
        name_input.send_keys(full_name)
        time.sleep(1)
        
        # Enter username
        username_input = driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(1)
        
        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(2)
        
        # Click Sign Up button
        signup_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        signup_button.click()
        logger.info("Submitted signup form")
        time.sleep(5)
        
        # Handle birthday page if appears
        try:
            month_select = driver.find_element(By.XPATH, "//select[@title='Month:']")
            if month_select:
                logger.info("Filling birthday...")
                month_select.send_keys("January")
                day_select = driver.find_element(By.XPATH, "//select[@title='Day:']")
                day_select.send_keys("15")
                year_select = driver.find_element(By.XPATH, "//select[@title='Year:']")
                year_select.send_keys("1995")
                next_button = driver.find_element(By.XPATH, "//button[contains(text(),'Next')]")
                next_button.click()
                time.sleep(3)
        except:
            pass
        
        # Get OTP from email
        otp = get_otp_from_temp_mail(email)
        if not otp:
            driver.quit()
            return "❌ Failed to receive OTP code"
        
        # Enter confirmation code
        try:
            otp_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            otp_input.clear()
            otp_input.send_keys(otp)
            time.sleep(1)
            
            confirm_button = driver.find_element(By.XPATH, "//button[contains(text(),'Next') or contains(text(),'Confirm')]")
            confirm_button.click()
            logger.info("OTP submitted")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error submitting OTP: {e}")
            driver.quit()
            return f"❌ Failed to submit OTP: {str(e)}"
        
        # Switch to Professional Account (Creator - Personal)
        try:
            logger.info("Switching to professional account...")
            driver.get("https://www.instagram.com/accounts/edit/")
            time.sleep(5)
            
            # Look for "Switch to Professional Account" button
            try:
                switch_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(),'Switch to professional account')]")
                ))
                switch_button.click()
                time.sleep(3)
            except:
                # Try alternative path through settings
                driver.get("https://www.instagram.com/accounts/convert_to_professional_account/")
                time.sleep(3)
            
            # Select "Creator" account type
            try:
                creator_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(),'Creator')]//ancestor::button")
                ))
                creator_button.click()
                time.sleep(2)
                
                # Click Next
                next_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Next')]")
                next_btn.click()
                time.sleep(3)
            except Exception as e:
                logger.error(f"Error selecting creator: {e}")
            
            # Select "Personal Blog" or "Personal" category
            try:
                personal_category = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(),'Personal') or contains(text(),'Blog')]//ancestor::button")
                ))
                personal_category.click()
                time.sleep(2)
                
                # Click Done
                done_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Done') or contains(text(),'Next')]")
                done_btn.click()
                time.sleep(3)
                
                logger.info("Successfully switched to creator account")
            except Exception as e:
                logger.error(f"Error selecting category: {e}")
            
            # Skip contact info, email options etc
            for _ in range(3):
                try:
                    skip_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Skip') or contains(text(),'Not Now')]")
                    skip_btn.click()
                    time.sleep(2)
                except:
                    break
                    
        except Exception as e:
            logger.error(f"Error switching to professional: {e}")
        
        driver.quit()
        
        result = f"""
✅ Instagram Account Created Successfully!

📧 Email: {email}
👤 Username: {username}
🔐 Password: {password}
👥 Name: {full_name}
💼 Type: Creator (Personal)
"""
        logger.info("Account created successfully")
        return result
        
    except Exception as e:
        if driver:
            driver.quit()
        logger.error(f"Error creating account: {e}")
        return f"❌ Error: {str(e)}"

# ========== TELEGRAM BOT HANDLERS ==========

def start(update: Update, context: CallbackContext):
    """Handle /start command"""
    welcome_msg = """
🤖 Instagram Account Creator Bot

Commands:
/create - Create a new Instagram account
/help - Show this help message

⚠️ Educational purposes only
"""
    update.message.reply_text(welcome_msg)

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    help_msg = """
📖 How to use:

1. Send /create to start account creation
2. Wait 2-3 minutes for the process
3. You'll receive account details

⏳ Each account takes ~2-3 minutes
📊 Accounts are created with Creator profile (Personal category)
"""
    update.message.reply_text(help_msg)

def create_account_command(update: Update, context: CallbackContext):
    """Handle /create command"""
    update.message.reply_text("🔄 Creating Instagram account...\n⏳ Please wait 2-3 minutes...")
    
    try:
        result = create_instagram_account()
        update.message.reply_text(result)
    except Exception as e:
        logger.error(f"Error in create command: {e}")
        update.message.reply_text(f"❌ An error occurred: {str(e)}")

def error_handler(update: Update, context: CallbackContext):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    logger.info("Starting bot...")
    
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("create", create_account_command))
    dp.add_error_handler(error_handler)
    
    # Start bot
    updater.start_polling()
    logger.info("Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()