from src.search_helper import graph_link
from dotenv import load_dotenv
import logging
from src.helper import login, start_chrome_with_debug, init_db, load_profiles_from_csv, load_profiles_from_json, load_profiles_from_txt
import sqlite3

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
    # Initialize SQLite database
    db_path = './data/profile_list.db'
    root_profiles_file = './data/root_profiles.json'
    init_db(db_path)
    
    # Load root profiles based on the file type
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
    
    # Load environment variables (if necessary)
    # load_dotenv(dotenv_path='./environment/.env')
    
    # Initialize the Selenium driver
    print("Starting Chrome with remote debugging...")
    logging.info("Starting Chrome with remote debugging...")
    driver = start_chrome_with_debug()
    
    try:
        # Run the graph_link function to scrape profiles
        logging.info("Starting profile scraping...")
        graph_link(driver, list_profile, './data/profile_list.db')  # Save scraped profiles to SQLite
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        
    finally:
        logging.info("Closing the Selenium driver...")
        # driver.quit()

if __name__ == "__main__":
    main()
