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
def save_to_json(data, filename="./data/scraped_profiles.json"):
    """
    Save the scraped data to a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}.")
    except Exception as e:
        logging.error(f"Error saving to JSON: {e}")

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
def save_scraped_profile(profile_url, scraped_profiles_file="./data/scraped_profiles.json"):
    try:
        with open(scraped_profiles_file, "r+", encoding="utf-8") as f:
            scraped_profiles = json.load(f)
            if profile_url not in scraped_profiles:
                scraped_profiles.append(profile_url)
                f.seek(0)
                json.dump(scraped_profiles, f, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        # If the file doesn't exist, create it
        with open(scraped_profiles_file, "w", encoding="utf-8") as f:
            json.dump([profile_url], f, ensure_ascii=False, indent=4)