import json
import logging
from helper import save_scraped_profile, save_to_json
from scrape import scrape_profile

def scrape_profiles_from_urls(driver, profile_urls_file="./data/employee_profiles.json", scraped_profiles_file="./data/scraped_profiles.json"):
    """
    Phase 2: Scrape profiles from a file of profile URLs.
    """
    # Load profile URLs
    with open(profile_urls_file, "r", encoding="utf-8") as f:
        profile_urls = json.load(f)

    # Load already scraped profiles
    try:
        with open(scraped_profiles_file, "r", encoding="utf-8") as f:
            scraped_profiles = json.load(f)
    except FileNotFoundError:
        scraped_profiles = []


    for profile_url in profile_urls:
        # Check if the profile has already been scraped
        if profile_url not in scraped_profiles:
            logging.info(f"Scraping profile: {profile_url}")
            profile_data = scrape_profile(driver, profile_url, visited_profiles=scraped_profiles)

            if profile_data:
                # Save the profile data (implement your saving logic here)
                save_to_json(profile_data, './data/scraped_profiles_data.json')

                # Mark the profile as scraped
                save_scraped_profile(profile_url, scraped_profiles_file)
            else:
                logging.warning(f"Failed to scrape profile: {profile_url}")
        else:
            logging.info(f"Profile already scraped: {profile_url}")

    driver.quit()
