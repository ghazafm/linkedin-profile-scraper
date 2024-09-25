import logging
from selenium import webdriver
from src.helper import start_chrome_with_debug
from src.company_scrape import (
    extract_company_people_links,
    save_employee_urls,
    read_company_urls,
)

# Setup logging for scraping URLs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./log/scraping.log"),
        # logging.StreamHandler()  # Log to console
    ],
)


def main():
    # driver = webdriver.Chrome()
    driver = start_chrome_with_debug()

    # Read company URLs from a file
    company_urls = read_company_urls("./data/company_list.txt")

    all_profile_urls = []
    for company_url in company_urls:
        profile_links = extract_company_people_links(driver, company_url)
        print(profile_links)
        all_profile_urls.extend(profile_links)

    # Save all profile URLs to a file
    save_employee_urls(all_profile_urls, "./data/employee_profiles.json")

    driver.quit()


if __name__ == "__main__":
    main()
