# Linkedin-Profile-Scraper

A LinkedIn profile scraper built using Selenium. The scraper logs into LinkedIn, extracts profile information (such as intro, experience, education, certificates, etc.), and saves the results in JSON format.

## Repository Structure

```bash
SCRAPER-LINKEDIN-PROFILE/
├── data/                   # Output folder for scraped data
│   └── scraped_profiles.json  # JSON file containing scraped LinkedIn profile data
├── dump/                   # Folder for storing temporary or intermediate files (currently empty)
├── environment/            # Environment-specific files
│   └── .env                # Environment variables file
├── log/                    # Logs folder for tracking scraping operations
│   └── scraping.log        # Log file for storing process logs
├── src/                    # Source code for the scraper
│   ├── helper.py           # Helper functions (login, saving data, etc.)
│   ├── main.py             # Main script for running the scraper
│   └── scrape.py           # Scraping functions for LinkedIn profile data
├── .gitignore              # Git ignore file (ensure sensitive files like .env are not pushed)
├── LICENSE                 # License file (if applicable)
└── README.md               # Project documentation (this file)
```

## Requirements

Before running the project, ensure you have the following installed:

- **Python 3.x**: You can download it [here](https://www.python.org/downloads/).
- **Google Chrome Browser**: Used by Selenium to automate browser actions.
- **ChromeDriver**: Make sure the ChromeDriver version matches your Chrome browser version. [Download ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads).
- **Selenium**: For browser automation.
- **MongoDB (Optional)**: If you want to store data directly in a MongoDB database.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-repository-link/scraper-linkedin-profile.git
cd scraper-linkedin-profile
```

### 2. Install Dependencies

Ensure you have `pip` installed and run the following command to install the necessary packages:

```bash
pip install -r requirements.txt
```

> Note: You may need to create a `requirements.txt` file if it's not present, containing at least `selenium`, `pymongo`, and `python-dotenv`.

### 3. Configure Environment Variables

Create a `.env` file in the `environment/` folder with the following variables:

```bash
# .env
EMAIL=your_linkedin_email
PASSWORD=your_linkedin_password
MONGO_URI=mongodb://localhost:27017  # MongoDB connection (optional)
MONGO_DB=linkedin_db                 # MongoDB database name (optional)
MONGO_COLLECTION=profiles            # MongoDB collection name (optional)
NUMBER_PROFILE_DISCOVERIES=5         # Number of profiles to scrape
TIMEOUT=10                           # Timeout for Selenium elements
TRIES=3                              # Retry attempts for failed operations
DELAY=2                              # Delay between retries
```

### 4. Running the Scraper

Run the main script to start scraping:

```bash
python src/main.py
```

### 5. Output

The scraped LinkedIn profiles will be saved in `data/scraped_profiles.json`. You can adjust this in the `helper.py` if you want to change the output format or location.

### 6. Logging

All logs related to the scraping process are stored in the `log/scraping.log` file. These logs are useful for debugging and tracking the progress of the scraper.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.