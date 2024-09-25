import os
import logging
from dotenv import load_dotenv
from selenium import webdriver
from helper import login, start_chrome_with_debug, save_to_json
from profile_scrape import scrape_profile, extract_more_profiles

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
    # Load environment variables
    load_dotenv()

    try:
        # Validate the NUMBER_PROFILE_DISCOVERIES environment variable
        number_of_profiles = os.getenv('NUMBER_PROFILE_DISCOVERIES')
        if not number_of_profiles:
            raise ValueError("Missing environment variable: NUMBER_PROFILE_DISCOVERIES")
        number_of_profiles = int(number_of_profiles)

        # Initialize the Selenium driver
        logging.info("Starting Chrome with remote debugging...")
        driver = start_chrome_with_debug()
        # driver = webdriver.Chrome()

        # Log in to LinkedIn
        driver.get('https://www.linkedin.com/login')
        # login(driver)

        profile_url = "https://www.linkedin.com/in/fauzanghaza"
        profile_data = []
        profile_discovered = []

        for i in range(number_of_profiles):
            logging.info(f"Processing profile number: {i+1}")
            if profile_url not in profile_discovered:
                try:
                    # Scrape the profile data
                    profile_info = scrape_profile(driver, profile_url, visited_profiles=profile_discovered)
                    if profile_info:
                        profile_data.append(profile_info)  # Append the scraped data
                        profile_discovered.append(profile_url)
                    else:
                        logging.warning(f"Failed to scrape profile: {profile_url}")

                    # Discover more profiles to scrape
                    profile_url = extract_more_profiles(driver)
                    if not profile_url:
                        logging.info("No more profiles found.")
                        break

                except Exception as e:
                    logging.error(f"Error while scraping profile {profile_url}: {e}")
                    continue  # Proceed to the next profile in case of an error

        # Save the collected data to a JSON file
        if profile_data:
            save_to_json(profile_data)
            logging.info("Profile data successfully saved to JSON.")
        else:
            logging.warning("No profile data to save.")

    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
    
    finally:
        # Quit the driver to close the browser
        if 'driver' in locals():
            driver.quit()
        logging.info("Driver successfully closed.")


if __name__ == "__main__":
    main()
