import time
import random
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from helper import (
    get_field_value,
    remove_existing_urls_from_master,
    append_to_json_list,
    create_fresh_json_file,
    write_str_to_txt_file,
    extract_and_save_preloaded_state
)


def get_soup_from_url(url):
    options = Options()

    # Do NOT use old --headless (more detectable)
    options.add_argument("--headless=new")

    # Remove obvious automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    # Realistic user agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)

        # Random human-like delay
        time.sleep(random.uniform(3, 6))

        # Scroll a bit (simulate user)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(1, 3))

        html = driver.page_source
        print(f"Fetched (Selenium) URL: {url}")

        return BeautifulSoup(html, "html.parser")

    finally:
        driver.quit()

def get_job_listings_from_soup(soup):
    # Adjust selector to actual site
    job_listings = soup.find_all('a', class_='res-1j9e5pd')
    print(f"Found {len(job_listings)} job listings on the page.")
    print(job_listings)
    return job_listings


def get_next_from_soup(soup):
    next_button = soup.find('a', class_='res-y58pif')
    
    if next_button:
        print(next_button.get('href'))
        return next_button.get('href')
    return None


def get_job_details_from_listing(listing):
    """
    Extract job details from a listing block.
    Adjust selectors according to real website.
    """

    try:
        title = listing.find('h2', class_='job-title').text.strip()
        company = listing.find('div', class_='company').text.strip()
        location = listing.find('div', class_='location').text.strip()
        job_url = listing.find('a')['href']

        print( {
            "job_title": title,
            "company": company,
            "location": location,
            "job_url": job_url
        })
        return {
            "job_title": title,
            "company": company,
            "location": location,
            "job_url": job_url
        }

    except Exception:
        return None


def process_job_listings():

    max_pages = get_field_value(
        "V_number_of_pages",
        "Job-Scrapers/stepstone/config.json"
    )
    print(get_field_value("start_link", "Job-Scrapers/indeed/configs.json"))
    current_url = get_field_value("start_link", "Job-Scrapers/indeed/configs.json")
    all_new_jobs = []

    pages_scraped = 0

    while current_url and (not max_pages or pages_scraped < max_pages):

        soup = get_soup_from_url(current_url)
        write_str_to_txt_file(soup.prettify(), f"Job-Scrapers/files/soup_{pages_scraped}.txt")
        listings = get_job_listings_from_soup(soup)

        for listing in listings:
            job = get_job_details_from_listing(listing)
            if job:
                all_new_jobs.append(job)

        current_url = get_next_from_soup(soup)
        pages_scraped += 1

    # Remove duplicates against master file
    filtered_jobs = remove_existing_urls_from_master(
        all_new_jobs,
        "master-input.json"
    )

    # Create fresh output file
    fresh_file = create_fresh_json_file()

    # Save filtered jobs
    append_to_json_list(fresh_file, filtered_jobs)
    append_to_json_list("master-input.json", filtered_jobs)
    append_to_json_list("pending-input.json", filtered_jobs)

    print(f"Saved {len(filtered_jobs)} new jobs to {fresh_file}")