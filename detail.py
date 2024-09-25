import logging
from selenium import webdriver
from src.profile_scrape import scrape_profiles_from_urls

# Setup logging for scraping profiles
logging.basicConfig(filename='./log/profile_scraping.log', level=logging.INFO)

def main():
    driver = webdriver.Chrome()
    # Scrape profiles from the URLs collected in Phase 1
    scrape_profiles_from_urls(driver)

if __name__ == "__main__":
    main()
