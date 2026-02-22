import time
import random
from bs4 import BeautifulSoup
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from helper import (
    get_field_value,
    append_to_json_list,
    create_fresh_json_file,
    write_str_to_txt_file,
    get_existing_urls
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

def get_next_from_soup(soup):
    next_button = soup.find('a', class_='res-1knl4qc')
    
    if next_button:
        print(next_button.get('href'))
        return next_button.get('href')
    return None

def get_job_urls_from_soup(soup):
    """
    Extract only job URLs from listing page.
    """
    listings = soup.find_all('a', class_='res-1j9e5pd')

    urls = []
    for listing in listings:
        href = listing.get("href")
        if href:
            urls.append("https://www.stepstone.de/" + href)

    print(f"Found {len(urls)} job URLs on page.")
    return urls

def scrape_job_detail_page(job_url):
    """
    Open job page and extract full details.
    """
    soup = get_soup_from_url(job_url)
    write_str_to_txt_file(soup.prettify(), f"Job-Scrapers/files/job_detail_{int(time.time())}.txt")
    try:
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Not specified"

        company = (
            soup.find("span", attrs={"data-at": "metadata-company-name"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-company-name"})
            else "Not specified"
        )

        location = (
            soup.find("span", attrs={"data-at": "metadata-location"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-location"})
            else "Not specified"
        )

        # --- Description from JSON-LD (safe) ---
        description = "Not specified"
        script_tag = soup.find("script", attrs={"type": "application/ld+json"})
        if script_tag and script_tag.string:
            data = json.loads(script_tag.string)
            desc_html = data.get("description", "")
            description = BeautifulSoup(desc_html, "html.parser").get_text(
                separator="\n", strip=True
            )


        employment_type = (
        soup.find("span", attrs={"data-at": "metadata-work-type"}).get_text(strip=True)
        if soup.find("span", attrs={"data-at": "metadata-work-type"})
        else "Not specified"
        )

        position = (
            soup.find("span", attrs={"data-at": "metadata-contract-type"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-contract-type"})
            else "Not specified"
        )

        job_location_type = (
            soup.find("span", attrs={"data-at": "metadata-location-type"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-location-type"})
            else "Not specified"
        )

        pay_per_hour = (
            soup.find("span", attrs={"data-at": "metadata-salary"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-salary"})
            else "Not specified"
        )

        job_data = {
            "job_title": title,
            "company": company,
            "location": location,
            "job_url": job_url,
            "job_description": description,
            "job_location_type": job_location_type,
            "employment_type": employment_type,
            "position": position,
            "pay_per_hour": pay_per_hour,
            "source": "stepstone"
        }

        print(f"Scraped: {title}")
        return job_data

    except Exception as e:
        print(f"Failed scraping {job_url}: {e}")
        return None


def process_job_listings():

    max_pages = get_field_value(
        "V_number_of_pages",
        "Job-Scrapers/stepstone/configs.json"
    )

    current_url = get_field_value(
        "start_link",
        "Job-Scrapers/stepstone/configs.json"
    )

    all_new_jobs = []

    # 🔥 Load master URLs ONCE
    existing_urls = get_existing_urls("Job-Scrapers/master-input.json")

    pages_scraped = 0

    while current_url and (not max_pages or pages_scraped < max_pages):

        soup = get_soup_from_url(current_url)
        write_str_to_txt_file(soup.prettify(), f"Job-Scrapers/files/page_{pages_scraped}_{int(time.time())}.txt")
        job_urls = get_job_urls_from_soup(soup)

        for job_url in job_urls:

            # 🚀 Skip before scraping
            if job_url in existing_urls:
                print(f"Skipping existing job: {job_url}")
                continue

            try:
                # Only now scrape detail page
                job_data = scrape_job_detail_page(job_url)

                if job_data:
                    all_new_jobs.append(job_data)
                    existing_urls.add(job_url)  # prevent duplicate in same run
                else:
                    print(f"⚠️ No data returned for: {job_url}")

            except Exception as e:
                print(f"❌ Failed scraping job details: {job_url}")
                print(f"   Reason: {e}")
                continue  # 🔥 important — move to next job

            if get_field_value("B_do_just_one", "Job-Scrapers/stepstone/configs.json"):
                break

        current_url = get_next_from_soup(soup)
        pages_scraped += 1

    if not all_new_jobs:
        print("No new jobs found.")
        return

    fresh_file = create_fresh_json_file()
    print(f"Created fresh file: {fresh_file}")
    append_to_json_list(fresh_file, all_new_jobs)
    append_to_json_list("Job-Scrapers/master-input.json", all_new_jobs)
    append_to_json_list("Job-Scrapers/pending-input.json", all_new_jobs)

    print(f"Saved {len(all_new_jobs)} new jobs.")