from collections import deque
import os
import logging
import time
from dotenv import load_dotenv
from selenium import webdriver
from src.helper import add_random_delay, init_db, load_profile_list, login, save_profile_list, start_chrome_with_debug, save_to_json, mimic_human_interaction, load_profiles_from_csv, load_profiles_from_json, load_profiles_from_txt
from src.scrape import scrape_profile, extract_more_profiles

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./log/scraping.log"),
        # logging.StreamHandler(),  # Log to console
    ]
)

def main():
    """
    Main function to perform LinkedIn profile scraping.
    It logs into LinkedIn, scrapes profiles, and saves the results to a JSON file.
    """
    max_profiles_per_hour = 50
    scraped_count = 0
    # Load environment variables
    load_dotenv(dotenv_path='./environment/.env')
    root_profiles_file = os.getenv("ROOT")
    db_path = os.getenv("DB_PATH")
    
    if root_profiles_file.endswith('.json'):
        list_profile = load_profiles_from_json(root_profiles_file)
    elif root_profiles_file.endswith('.txt'):
        list_profile = load_profiles_from_txt(root_profiles_file)
    elif root_profiles_file.endswith('.csv'):
        list_profile = load_profiles_from_csv(root_profiles_file)
    else:
        logging.error("Unsupported file format for root profiles.")
        return
    
    if not list_profile:
        logging.warning("No root profiles found in the file, starting with an empty set.")
    
    try:
        # Initialize the Selenium driver
        logging.info("Starting Chrome with remote debugging...")
        driver = start_chrome_with_debug()

        # Initialize database and queue
        init_db(db_path)
        queue = deque(list_profile)
        list_profile = load_profile_list(db_path)

        while queue:
            if scraped_count >= max_profiles_per_hour:
                logging.info("Reached hourly limit. Pausing for 1 hour...")
                time.sleep(3600)  # Sleep for 1 hour
                scraped_count = 0
            
            # add_random_delay()
            current_profile = queue.popleft()
            # mimic_human_interaction(driver)
            if current_profile not in list_profile:
                try:
                    # Scrape the profile data
                    profile_info = scrape_profile(driver, current_profile, visited_profiles=list_profile)
                    if profile_info:
                        list_profile.add(current_profile)
                        # Save each profile after scraping, appending to the file
                        save_to_json(profile_info)
                        logging.info(f"Profile {current_profile} successfully saved.")

                    else:
                        logging.warning(f"Failed to scrape profile: {current_profile}")

                    # Discover more profiles to scrape
                    new_links = extract_more_profiles(driver)
                    new_links = [link for link in new_links if link not in list_profile]
                    queue.extend(new_links)

                    
                    save_profile_list(db_path, current_profile)
                    
                    logging.info(f"Scraped profile: {current_profile}")
                    scraped_count += 1

                except Exception as e:
                    logging.error(f"Error while scraping profile {current_profile}: {e}")
                    continue  # Proceed to the next profile in case of an error

    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
    
    finally:
        # Quit the driver to close the browser
        if 'driver' in locals():
            driver.quit()
        logging.info("Driver successfully closed.")



if __name__ == "__main__":
    main()
