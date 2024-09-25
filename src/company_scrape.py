import json
import logging
from selenium.webdriver.common.by import By
from src.helper import get_objects
from src.helper import scroll_and_load, extract_elements

# Setup logging: log both to file and console
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./log/scraping.log"),  
        # logging.StreamHandler()  # Log to console
    ]
)

def extract_company_people_links(driver, company_url):
    """
    Extracts profile links from the company's 'People' section.
    Args:
        driver: Selenium WebDriver instance.
        company_url: URL of the company's LinkedIn page.

    Returns:
        A list of profile URLs for employees.
    """
    driver.get(company_url + "people/")

    # Scroll through the "People" page to load all profiles (customize scrolling logic if needed)
    scroll_and_load(driver, wait_time=4, max_scrolls=10)

    # Locate profile links in the "People" section
    profile_links_xpath = "//ul[@class='display-flex list-style-none flex-wrap']//li[@class='grid grid__col--lg-8 block org-people-profile-card__profile-card-spacing']"
    profile_links = get_objects(driver, By.XPATH, profile_links_xpath)
    for link in profile_links:
        print(link)
    # Extract the href (profile link) from each element
    return [extract_elements(link, By.XPATH, ".", attribute='href') for link in profile_links]

def save_employee_urls(employee_urls, file_path="./data/employee_profiles.json"):
    """
    Save the collected employee profile URLs to a JSON file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(employee_urls, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved {len(employee_urls)} employee profile URLs.")
    except Exception as e:
        logging.error(f"Error saving employee URLs: {e}")


def read_company_urls(file_path):
    """
    Reads company URLs from a file and returns them as a list.
    Args:
        file_path: Path to the file containing the company URLs.
    Returns:
        A list of company URLs.
    """
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]