import logging
from urllib.parse import urlparse, urlunparse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from helper import scroll_and_load, get_object, get_objects, extract_elements


# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./log/scraping.log"),  # Log to file
        # logging.StreamHandler(),  # Log to console
    ]
)


def extract_intro(driver):
    """
    Extracts the introduction section from the LinkedIn profile.
    """
    intro_data = {}

    try:
        intro_xpath = "//div[contains(@class, 'mt2 relative')]"
        intro = get_object(driver, By.XPATH, intro_xpath)

        if intro:
            # Extract name
            name_xpath = ".//h1[contains(@class, 'text-heading-xlarge')]"
            intro_data["name"] = extract_elements(intro, By.XPATH, name_xpath)

            # Extract pronouns
            pronouns_xpath = ".//span[contains(@class, 'text-body-small v-align-middle')]"
            intro_data["pronouns"] = extract_elements(intro, By.XPATH, pronouns_xpath)

            # Extract workplace
            works_at_xpath = ".//div[contains(@class, 'text-body-medium break-words')]"
            intro_data["works_at"] = extract_elements(intro, By.XPATH, works_at_xpath)

            # Extract location
            location_xpath = ".//span[contains(@class, 'text-body-small inline t-black--light break-words')]"
            intro_data["location"] = extract_elements(intro, By.XPATH, location_xpath)

            # Extract followers and connections
            followers_xpath = "//p[contains(@class, 'pvs-header__optional-link')]//span[contains(text(), 'followers')]"
            connections_xpath = "//li[@class='text-body-small']//span[@class='t-bold']"
            intro_data["followers"] = extract_elements(driver, By.XPATH, followers_xpath).split()[0]
            intro_data["connections"] = extract_elements(driver, By.XPATH, connections_xpath)

        else:
            logging.error("Intro section not found.")
            return None

    except NoSuchElementException:
        logging.error("Error extracting intro: Element not found.")
        return None
    except TimeoutError:
        logging.error("Timeout: Failed to load intro.")
        return None
    except Exception as e:
        logging.error(f"Error extracting intro: {e}")
        return None

    return intro_data


def extract_about(driver):
    """
    Extracts the 'About' section from the LinkedIn profile.
    """
    try:
        xpath_about = "//section[contains(@class, 'artdeco-card pv-profile-card')]//h2[span[text()='About']]/ancestor::section//div[contains(@class, 'full-width')]//span[@aria-hidden='true']"
        about_description = extract_elements(driver, By.XPATH, xpath_about)

        return {"about_description": about_description or ""}
    except Exception:
        logging.error("Error: 'About' section not available.")
        return {"about_description": ""}


def extract_experience(driver):
    """
    Extracts the 'Experience' section from the LinkedIn profile.
    """
    experience_data = []
    try:
        scroll_and_load(driver)

        experience_elements = get_objects(
            driver, By.XPATH,
            "//div[@id='experience']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]"
        )

        for experience in experience_elements:
            experience_dict = {}

            nested_experiences = get_objects(
                experience, By.XPATH,
                ".//div[contains(@class, 'pvs-entity__sub-components')]/ul/li/div[contains(@data-view-name, 'profile-component-entity')]"
            ) or None

            if nested_experiences:
                company_name = extract_elements(experience, By.XPATH, ".//div[contains(@class, 'flex-wrap')]").split("\n")[0]
                location = extract_elements(experience, By.XPATH, ".//a[@data-field='experience_company_logo']//span[contains(@class, 't-black--light')]").split("\n")[0]

                for nested_exp in nested_experiences:
                    job_title = extract_elements(nested_exp, By.XPATH, ".//div[@class='display-flex flex-wrap align-items-center full-height']").split("\n")[0]
                    type = extract_elements(nested_exp, By.XPATH, ".//span[@class='t-14 t-normal']").split()[0]
                    dates = extract_elements(nested_exp, By.XPATH, './/span[contains(@class, "t-black--light")]/span')
                    description = extract_elements(nested_exp, By.XPATH, ".//div[contains(@class,'inline-show-more-text--is-collapsed') and not(contains(@class, 'break-words'))]")

                    experience_dict = {
                        "company_name": company_name,
                        "job_title": job_title,
                        "location": location,
                        "type": type,
                        "dates": dates,
                        "description": description
                    }
                    experience_data.append(experience_dict)

            else:
                company_type = extract_elements(experience, By.XPATH, ".//span[@class='t-14 t-normal']").split("\n")[0].split("·")
                company_name, type = company_type[0], company_type[1]
                job_title = extract_elements(experience, By.XPATH, ".//div[contains(@class, 'flex-wrap')]")
                dates = extract_elements(experience, By.XPATH, './/span[contains(@class, "t-black--light")]/span')
                location = extract_elements(experience, By.XPATH, ".//span[contains(@class, 't-black--light')]//span[@aria-hidden='true']")
                description = extract_elements(experience, By.XPATH, ".//li[contains(@class, 'pvs-list__item--with-top-padding')]//div[contains(@class, 'inline-show-more-text--is-collapsed')]")

                experience_data.append({
                    "company_name": company_name,
                    "job_title": job_title,
                    "location": location,
                    "type": type,
                    "dates": dates,
                    "description": description
                })

    except Exception:
        logging.error("Error extracting experience section.")
    return experience_data


def extract_education(driver):
    """
    Extracts the 'Education' section from the LinkedIn profile.
    """
    educations = []
    try:
        education_entries = get_objects(driver, By.XPATH, "//div[@id='education']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for entry in education_entries:
            education_data = {}

            # Extract institution name
            institution_xpath = ".//a[contains(@target, '_self')]//span[contains(@aria-hidden, 'true')]"
            education_data["institution"] = extract_elements(entry, By.XPATH, institution_xpath)

            # Extract degree and field of study
            degree_field_xpath = ".//span[contains(@class, 't-14 t-normal')]"
            education_data["degree_field"] = extract_elements(entry, By.XPATH, degree_field_xpath)

            # Extract graduation year
            graduation_year_xpath = ".//span[@class='pvs-entity__caption-wrapper']"
            education_data["graduation_year"] = extract_elements(entry, By.XPATH, graduation_year_xpath)

            educations.append(education_data)

    except Exception:
        logging.error("Error extracting education information.")
    return educations


def extract_certificates(driver):
    """
    Extracts the 'Licenses & Certifications' section from the LinkedIn profile.
    """
    certificates = []
    try:
        certificate_entries = get_objects(driver, By.XPATH, "//div[@id='licenses_and_certifications']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for entry in certificate_entries:
            certificate_data = {}

            # Extract certificate name
            cert_name_xpath = ".//div[contains(@class, 'display-flex')]//span[contains(@aria-hidden, 'true')]"
            certificate_data["cert_name"] = extract_elements(entry, By.XPATH, cert_name_xpath)

            # Extract issuing organization
            issuer_xpath = ".//span[@class='t-14 t-normal']//span[contains(@aria-hidden, 'true')]"
            certificate_data["issuer"] = extract_elements(entry, By.XPATH, issuer_xpath)

            # Extract issue date
            issue_date_xpath = ".//span[@class='pvs-entity__caption-wrapper' and contains(@aria-hidden, 'true')]"
            certificate_data["issue_date"] = extract_elements(entry, By.XPATH, issue_date_xpath)

            # Extract credential URL (if available)
            credential_url_xpath = ".//a[contains(@class, 'artdeco-button')]"
            certificate_data["credential_url"] = extract_elements(entry, By.XPATH, credential_url_xpath, attribute="href")

            certificates.append(certificate_data)

    except Exception:
        logging.error("Error extracting certificates information.")
    return certificates


def extract_project(driver):
    """
    Extracts the 'Projects' section from the LinkedIn profile.
    """
    projects = []
    try:
        project_elements = get_objects(driver, By.XPATH, "//div[@id='projects']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for project in project_elements:
            project_data = {}

            # Extract project title
            title_xpath = ".//div[contains(@class, 'mr1 t-bold')]/span[@aria-hidden='true']"
            project_data["project_title"] = extract_elements(project, By.XPATH, title_xpath)

            # Extract project dates
            dates_xpath = ".//span[@class='t-14 t-normal']"
            project_data["dates"] = extract_elements(project, By.XPATH, dates_xpath)

            # Extract associated organization
            organization_xpath = ".//span[contains(text(), 'Associated with')]/following-sibling::span"
            project_data["organization"] = extract_elements(project, By.XPATH, organization_xpath)

            # Extract project description
            description_xpath = ".//span[@aria-hidden='true']"
            project_data["description"] = extract_elements(project, By.XPATH, description_xpath)

            # Extract project link (if available)
            link_xpath = ".//a[@class='optional-action-target-wrapper']"
            project_data["link"] = extract_elements(project, By.XPATH, link_xpath, attribute="href")

            projects.append(project_data)

    except Exception:
        logging.error("Error extracting project information.")
    return projects


def extract_volunteering(driver):
    """
    Extracts the 'Volunteering' section from the LinkedIn profile.
    """
    volunteers = []
    try:
        volunteering_entries = get_objects(driver, By.XPATH, "//div[@id='volunteering_experience']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for entry in volunteering_entries:
            volunteer_data = {}

            # Extract role
            role_xpath = ".//div[contains(@class,'t-bold')]"
            volunteer_data["role"] = extract_elements(entry, By.XPATH, role_xpath)

            # Extract organization
            organization_xpath = ".//span[contains(@class, 't-14 t-normal')]"
            volunteer_data["organization"] = extract_elements(entry, By.XPATH, organization_xpath)

            # Extract duration
            duration_xpath = ".//span[@class='pvs-entity__caption-wrapper']"
            volunteer_data["duration"] = extract_elements(entry, By.XPATH, duration_xpath)

            volunteers.append(volunteer_data)

    except Exception:
        logging.error("Error extracting volunteering information.")
    return volunteers


def extract_skill(driver):
    """
    Extracts the 'Skills' section from the LinkedIn profile.
    """
    skills = []
    try:
        skill_elements = get_objects(driver, By.XPATH, "//div[@id='skills']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for skill in skill_elements:
            skill_data = {}

            # Extract skill title
            title_xpath = ".//div[contains(@class, 'hoverable-link-text')]/span[@aria-hidden='true']"
            skill_data["title"] = extract_elements(skill, By.XPATH, title_xpath)

            # Extract endorsements count
            endorsements_xpath = ".//span[contains(@aria-hidden, 'true') and contains(text(), 'endorsements')]"
            skill_data["endorsements"] = extract_elements(skill, By.XPATH, endorsements_xpath).split()[0]

            skills.append(skill_data)

    except Exception:
        logging.error("Error extracting skills information.")
    return skills


def extract_honor(driver):
    """
    Extracts the 'Honors & Awards' section from the LinkedIn profile.
    """
    honors = []
    try:
        honors_xpath = "//div[@id='honors_and_awards']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]"
        honor_elements = get_objects(driver, By.XPATH, honors_xpath)

        for honor in honor_elements:
            honor_data = {}

            # Extract honor title
            title_xpath = ".//div[contains(@class, 't-bold')]/span"
            honor_data["title"] = extract_elements(honor, By.XPATH, title_xpath)

            # Extract issuing organization
            issuer_xpath = ".//span[contains(@class, 't-14 t-normal')]"
            issuer_data = extract_elements(honor, By.XPATH, issuer_xpath).split("·")
            honor_data["issuer"] = issuer_data[0].strip()
            honor_data["issued_date"] = issuer_data[1].strip()

            honors.append(honor_data)

    except Exception:
        logging.error("Error extracting honors information.")
    return honors


def extract_organizations(driver):
    """
    Extracts the 'Organizations' section from the LinkedIn profile.
    """
    organizations = []
    try:
        organization_entries = get_objects(driver, By.XPATH, "//div[@id='organizations']/ancestor::section//ul/li[contains(@class, 'artdeco-list__item')]")

        for entry in organization_entries:
            organization_data = {}

            # Extract organization name
            name_xpath = ".//div[contains(@class,'t-bold')]"
            organization_data["organization_name"] = extract_elements(entry, By.XPATH, name_xpath)

            # Extract role and duration
            role_duration_xpath = ".//span[contains(@class, 't-14 t-normal')]"
            role_duration = extract_elements(entry, By.XPATH, role_duration_xpath).split("·")
            organization_data["role"] = role_duration[0].strip() if len(role_duration) > 0 else None
            organization_data["duration"] = role_duration[1].strip() if len(role_duration) > 1 else None

            # Extract description
            description_xpath = ".//li[contains(@class, 'pvs-list__item--with-top-padding')]//div[contains(@class, 't-14 t-normal t-black')]"
            organization_data["description"] = extract_elements(entry, By.XPATH, description_xpath)

            organizations.append(organization_data)

    except Exception:
        logging.error("Error extracting organizations information.")
    return organizations


def scrape_profile(driver, profile_url, visited_profiles):
    """
    Scrapes a LinkedIn profile by extracting all relevant sections (intro, about, experience, education, etc.).
    
    Args:
        driver: Selenium WebDriver instance.
        profile_url: URL of the LinkedIn profile to scrape.
        visited_profiles: A set containing previously visited profile URLs.

    Returns:
        profile_data: A dictionary containing all extracted profile sections (intro, experience, etc.).
    """

    if profile_url in visited_profiles:
        logging.warning(f"Profile already visited: {profile_url}")
        return None

    logging.info(f"Scraping profile: {profile_url}")
    
    # Visit the profile URL
    # driver.get(profile_url)
    
    # Scroll to load the entire page content
    scroll_and_load(driver)

    # Initialize dictionary to store all profile data
    profile_data = {}

    # Extract different sections of the profile
    try:
        profile_data["intro"] = extract_intro(driver)
        profile_data["about"] = extract_about(driver)
        profile_data["experience"] = extract_experience(driver)
        profile_data["education"] = extract_education(driver)
        profile_data["certificates"] = extract_certificates(driver)
        profile_data["projects"] = extract_project(driver)
        profile_data["volunteering"] = extract_volunteering(driver)
        profile_data["skills"] = extract_skill(driver)
        profile_data["honors"] = extract_honor(driver)
        profile_data["organizations"] = extract_organizations(driver)

        logging.info(f"Successfully scraped profile: {profile_url}")

    except Exception as e:
        logging.error(f"Failed to scrape profile {profile_url}: {e}")
        profile_data = None

    return profile_data


def extract_more_profiles(driver):
    """
    Extracts URLs of profiles from the 'More profiles for you' section.
    """
    try:
        profile_urls = get_objects(driver, By.XPATH, "//a[@data-field='browsemap_card_click']")
        return [urlparse(url.get_attribute('href'))._replace(query="").geturl() for url in profile_urls] if profile_urls else []
    except NoSuchElementException:
        logging.error("No 'More profiles for you' section found.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return []


def extract_company_people_links(driver, company_url):
    """
    Extracts profile links from a company's 'People' page.
    """
    driver.get(company_url)
    profile_links_xpath = "//ul[@class='display-flex list-style-none flex-wrap']/li//a[contains(@class, 'app-aware-link')]"
    profile_links = get_objects(driver, By.XPATH, profile_links_xpath)

    return [extract_elements(profile, By.XPATH, ".", attribute="href") for profile in profile_links]