import os
import time
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import logging
from functools import wraps
import sqlite3
import random
import csv
from selenium.webdriver.common.action_chains import ActionChains
# Load environment variables
load_dotenv(dotenv_path='./environment/.env')
timeout = int(os.getenv("TIMEOUT"))
TRIES = int(os.getenv('TRIES'))
DELAY = float(os.getenv('DELAY'))
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Setup logging: log both to file and console
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./log/scraping.log"),  
        # logging.StreamHandler()  # Log to console
    ]
)

# Retry decorator for retrying functions that may fail
def retry(ExceptionToCheck, tries=TRIES, delay=DELAY):
    """
    Retry decorator to handle exceptions and retry failed functions.
    Logs more concise exception messages for brevity.
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    logging.warning(f"Retrying after exception: {type(e).__name__})")
                    time.sleep(mdelay)
                    mtries -= 1
            logging.error(f"Failed after {tries} attempts.")
            return None
        return f_retry
    return deco_retry



# 1. Browser Initialization & Login
@retry(ExceptionToCheck=(NoSuchElementException, TimeoutException), tries=TRIES, delay=DELAY)
def login(driver):
    """
    Perform login on the target website using credentials from environment variables.
    If CAPTCHA is detected, the user is prompted to manually complete it before the script proceeds.

    Args:
        driver: Selenium WebDriver instance for browser interaction.
    
    Steps:
        1. Fill in the email and password from environment variables.
        2. Click the login button.
        3. Check for the presence of a CAPTCHA.
        4. If a CAPTCHA is detected, the script pauses, allowing the user to manually solve it.
        5. Once the CAPTCHA is solved, the user presses Enter to continue execution.
        6. Verify if the login was successful by checking for a post-login element.
    """
    email = EMAIL
    password = PASSWORD

    try:
        username = get_object(driver, By.ID, "username")
        username.send_keys(email)
        logging.info("Entered email successfully.")

        password_element = get_object(driver, By.XPATH, "//input[@id='password' and @name='session_password']")
        password_element.send_keys(password)
        logging.info("Entered password successfully.")
    except Exception as e:
        logging.error(f"Error entering login credentials: {e}")
        return

    try:
        login_button = get_object(driver, By.CLASS_NAME, "btn__primary--large")
        login_button.click()
        logging.info("Login button clicked.")
    except NoSuchElementException as e:
        logging.error(f"Login button not found: {e}")
        return

    try:
        captcha_xpath = "//input[@id='captcha' or @class='captcha']"  # Adjust this XPath to the actual CAPTCHA element
        captcha_element = driver.find_elements(By.XPATH, captcha_xpath)
        
        if captcha_element:
            logging.info("CAPTCHA detected. Waiting for user to complete CAPTCHA.")
            input("Please complete the CAPTCHA in the browser and press Enter to continue...")
            logging.info("User completed CAPTCHA.")

        profile_xpath = "//div[@id='profile']"
        profile_element = driver.find_elements(By.XPATH, profile_xpath)

        if profile_element:
            logging.info("Login successful.")
        else:
            logging.warning("Login may have failed. Please check the credentials or CAPTCHA.")
    
    except Exception as e:
        logging.error(f"Error during CAPTCHA handling or login verification: {e}")


@retry(ExceptionToCheck=(NoSuchElementException, TimeoutException), tries=TRIES, delay=DELAY)
def scroll_and_load(driver, wait_time=2, max_scrolls=None):
    """
    Scroll down the page and click the 'Show more results' button if available.
    Useful for loading dynamic content.
    
    Args:
        driver: Selenium WebDriver instance.
        wait_time: Time to wait after each scroll (default is 2 seconds).
        max_scrolls: Maximum number of scrolls. If None, scroll infinitely (default behavior).
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while True:
        # Scroll down to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)  # Wait for the page to load

        # Try to click the "Show more results" button, if available
        try:
            show_more_button = get_object(driver, By.XPATH, "//button[@id='ember861']")
            if show_more_button:
                show_more_button.click()
                time.sleep(wait_time)  # Allow time for new content to load
        except NoSuchElementException:
            pass  # Button not found; continue scrolling

        new_height = driver.execute_script("return document.body.scrollHeight")

        # Break the loop if the page height hasn't increased (end of scrollable content)
        if new_height == last_height:
            break

        last_height = new_height
        scroll_count += 1

        # Stop if the maximum number of scrolls has been reached
        if max_scrolls and scroll_count >= max_scrolls:
            logging.info(f"Reached the maximum scroll limit of {max_scrolls}.")
            break


# 2. Selenium Utility Functions for Element Handling

def wait_element(driver, by, element, timeout=timeout):
    """
    Wait until a specific element is present on the page.
    """
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, element)))

def get_element(driver, by, element, timeout=timeout):
    """
    Get a single element from the page.
    """
    wait_element(driver, by, element, timeout)
    return driver.find_element(by, element)

def get_elements(driver, by, element, timeout=timeout):
    """
    Get multiple elements from the page.
    """
    wait_element(driver, by, element, timeout)
    return driver.find_elements(by, element)

@retry(ExceptionToCheck=(NoSuchElementException, TimeoutException), tries=TRIES, delay=DELAY)
def get_object(driver, by, element, timeout=timeout):
    """
    Wrapper around get_element with retry.
    """
    return get_element(driver, by, element, timeout)

@retry(ExceptionToCheck=(NoSuchElementException, TimeoutException), tries=TRIES, delay=DELAY)
def get_objects(driver, by, element, timeout=timeout):
    """
    Wrapper around get_elements with retry.
    """
    return get_elements(driver, by, element, timeout)


# 3. Data Extraction
@retry(ExceptionToCheck=(NoSuchElementException, TimeoutException), tries=TRIES, delay=DELAY)
def extract_elements(driver, by, element, multiple=False, attribute=None, timeout=timeout):
    """
    Extract the text or attribute of a web element. Supports both single and multiple elements.
    """
    elements = get_objects(driver, by, element, timeout) if multiple else [get_object(driver, by, element, timeout)]

    if attribute:
        if not multiple:
            return elements[0].get_attribute(attribute) if elements[0] else None
        return [el.get_attribute(attribute) for el in elements if el]

    if not multiple:
        return elements[0].text.strip() if elements[0] else None

    return [el.text.strip() for el in elements if el]


# 4. Data Storage
# def save_to_json(data, filename="./data/profile_list.json"):
#     """
#     Save the scraped data to a JSON file.
#     """
#     try:
#         with open(filename, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=4)
#         logging.info(f"Data saved to {filename}.")
#     except Exception as e:
#         logging.error(f"Error saving to JSON: {e}")
        

def save_to_json(profile_info, file_path='./data/scraped_profiles.json'):
    """
    Save a single profile's data to a JSON file, appending it one by one.
    If the file doesn't exist, it will create one. 
    If the file exists, it will append to the existing data.
    """
    if not os.path.exists(file_path):
        # Create the file if it doesn't exist and write the first profile
        with open(file_path, 'w') as file:
            json.dump([profile_info], file, indent=4)
    else:
        # If the file exists, load the current data, append the new profile, and save
        with open(file_path, 'r+') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
            data.append(profile_info)
            file.seek(0)
            json.dump(data, file, indent=4)


def save_to_mongo(data):
    """
    Save the scraped data to a MongoDB collection.
    """
    try:
        with MongoClient(MONGO_URI) as client:
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            if isinstance(data, list):
                collection.insert_many(data)
            else:
                collection.insert_one(data)
        logging.info(f"Data successfully saved to MongoDB collection: {COLLECTION_NAME}")
    except Exception as e:
        logging.error(f"Failed to save data to MongoDB: {e}")

def import_json_to_mongo(json_file_path, db_name, collection_name, mongo_uri="mongodb://localhost:27017/"):
    """
    Import a JSON file into a MongoDB collection.
    """
    try:
        with MongoClient(mongo_uri) as client:
            db = client[db_name]
            collection = db[collection_name]

            with open(json_file_path, "r") as file:
                data = json.load(file)

            if isinstance(data, list):
                collection.insert_many(data)
            else:
                collection.insert_one(data)

        logging.info(f"Data imported to {db_name}.{collection_name} successfully.")
    except Exception as e:
        logging.error(f"Failed to import JSON data to MongoDB: {e}")


# 5. Browser Setup
def start_chrome_with_debug():
    """
    Start Chrome with remote debugging enabled.
    """
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# Crawling
def save_profile_list(db_path, profile_url):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO profile_list (profile_url) VALUES (?)", (profile_url,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()
    
# Load scraped profiles from SQLite
def load_profile_list(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT profile_url FROM PROFILE_LIST")
    profile_list = set([row[0] for row in cursor.fetchall()])
    
    conn.close()
    return profile_list
    

def is_profile_scraped(db_path, profile_url):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT profile_url FROM PROFILE_LIST WHERE profile_url = ?", (profile_url,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result is not None
            
            


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    

    # Create table for scraped profiles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PROFILE_LIST (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_url TEXT UNIQUE NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    



# Function to load root profiles from a JSON file
def load_profiles_from_json(file_path):
    try:
        with open(file_path, 'r') as file:
            profiles = json.load(file)  # Load profiles from JSON
            logging.info(f"Loaded {len(profiles)} profiles from {file_path}")
            return set(profiles)  # Return as a set
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return set()

# Function to load root profiles from a TXT file (one URL per line)
def load_profiles_from_txt(file_path):
    try:
        with open(file_path, 'r') as file:
            profiles = {line.strip() for line in file}  # Remove extra whitespace and return as set
            logging.info(f"Loaded {len(profiles)} profiles from {file_path}")
            return profiles
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return set()

# Function to load root profiles from a CSV file
def load_profiles_from_csv(file_path):
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            profiles = {row[0].strip() for row in reader if row}  # Read first column, return as set
            logging.info(f"Loaded {len(profiles)} profiles from {file_path}")
            return profiles
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return set()
    
    
def add_random_delay(min_time=5, max_time=30):
    """Adds a random delay to mimic human-like pauses."""
    delay = random.uniform(min_time, max_time)
    time.sleep(delay)
    

def mimic_human_interaction(driver):
    """Mimics human interaction by randomly moving the mouse and scrolling."""
    # action = ActionChains(driver)
    # x_offset = random.randint(100, 250)
    # y_offset = random.randint(100, 250)
    # action.move_by_offset(x_offset, y_offset).perform()
    
    # Scroll randomly
    scroll_distance = random.randint(50, 100)
    driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
    add_random_delay()
    
    