import json
from src.scrape import extract_more_profiles
from collections import deque
from src.helper import load_profile_list, save_profile_list, add_random_delay, init_db, mimic_human_interaction
import time


def graph_link(driver, list_profile, db_path):
    max_profiles_per_hour = 50
    scraped_count = 0

    init_db(db_path)
    queue = deque(list_profile)
    list_profile = load_profile_list(db_path)

    while queue:
        if scraped_count >= max_profiles_per_hour:
            print("Reached hourly limit. Pausing for 1 hour...")
            time.sleep(3600)  # Sleep for 1 hour
            scraped_count = 0

        current_profile = queue.popleft()
        add_random_delay()

        # Only scrape if this profile hasn't been scraped before
        if current_profile not in list_profile:
            driver.get(current_profile)
            mimic_human_interaction(driver)

            # Scrape new profiles from the current page
            new_links = extract_more_profiles(driver)

            # Filter out already scraped profiles
            new_links = [link for link in new_links if link not in list_profile]

            # Add new links to the queue for further scraping
            queue.extend(new_links)

            # Add current profile to the scraped set and save it to the database
            list_profile.add(current_profile)
            save_profile_list(db_path, current_profile)

            print(f"Scraped profile: {current_profile}")
            scraped_count += 1

    print(f"Scraping completed. Total profiles scraped: {len(list_profile)}")
