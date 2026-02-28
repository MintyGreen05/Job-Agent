import time
import random
from bs4 import BeautifulSoup
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs


from Job_Scrapers.helper import (
    get_field_value,
    append_to_json_list,
    create_fresh_json_file,
    write_str_to_txt_file,
    get_existing_urls
)

generate_files = get_field_value("B_generate_files", "Job_Scrapers/indeed/configs.json")
do_one = get_field_value("B_do_just_one", "Job_Scrapers/indeed/configs.json")


def get_soup_from_url(url,driver):
    

    try:
        driver.get(url)

        # Random human-like delay
        time.sleep(random.uniform(3, 6))

        # Scroll a bit (simulate user)
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight/{random.uniform(2, 3)});")
        time.sleep(random.uniform(1, 3))

        html = driver.page_source
        print(f"Fetched (Selenium) URL: {url}")

        return BeautifulSoup(html, "html.parser")

    except Exception as e:
        print(f"Error fetching URL with Selenium: {e}")
        return None

def get_next_from_soup(soup):
    next_button = soup.find('a', attrs={'data-testid': 'pagination-page-next'})
    if next_button:
        href = next_button.get('href')
        full_url = "https://de.indeed.com/" + href
        print(full_url)
        return full_url

def get_job_urls_from_soup(soup):
    """
    Extract only job URLs from listing page.
    """
    listings = [
    a for a in soup.find_all("a", attrs={"data-jk": True})
    if a.get("href", "").startswith("/rc/clk?")
    ]

    urls = []
    for listing in listings:
        href = listing.get("href")
        parsed = urlparse(href)
        query = parse_qs(parsed.query)
        job_key = query.get("jk", [None])[0]
        if href:
            urls.append(f"https://de.indeed.com/viewjob?jk={job_key}")

    print(f"Found {len(urls)} job URLs on page.")
    return urls

def scrape_job_detail_page(job_url,driver):
    

    """
    Open job page and extract full details.
    """
    soup = get_soup_from_url(job_url,driver)
    if generate_files:
        write_str_to_txt_file(soup.prettify(), f"Job_Scrapers/files/job_detail_{int(time.time())}.txt")
    try:

        title = (
        soup.find("h1", attrs={"data-testid": "jobsearch-JobInfoHeader-title"})
            .get_text(strip=True)
        if soup.find("h1", attrs={"data-testid": "jobsearch-JobInfoHeader-title"})
        else "Not specified"
        )

        company = (
            soup.find("a", href=lambda x: x and "/cmp/" in x).get_text(strip=True)
            if soup.find("a", href=lambda x: x and "/cmp/" in x)
            else "Not specified"
        )

        location = (
            soup.find("div", attrs={"data-testid": "inlineHeader-companyLocation"}).get_text(strip=True)
            if soup.find("div", attrs={"data-testid": "inlineHeader-companyLocation"})
            else "Not specified might be in description"
        )

        # --- Description from JSON-LD (safe) ---
        description = "Not specified"
        desc_tag = soup.find("div", attrs={"id": "jobDescriptionText"})
        if desc_tag:
            description = desc_tag.get_text(separator="\n", strip=True)


        employment_type = (
            soup.find("div", attrs={"id": "salaryInfoAndJobType"})
                .find_all("span")[1]
                .get_text(strip=True)
            if soup.find("div", attrs={"id": "salaryInfoAndJobType"})
            else "Not specified might be in description"
        )

        position = (
            soup.find("span", attrs={"data-at": "metadata-contract-type"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-contract-type"})
            else "Not specified might be in description"
        )

        job_location_type = (
            soup.find("span", attrs={"data-at": "metadata-location-type"}).get_text(strip=True)
            if soup.find("span", attrs={"data-at": "metadata-location-type"})
            else "Not specified might be in description"
        )

        pay_per_hour = (
            soup.find("div", attrs={"id": "salaryInfoAndJobType"})
                .find_all("span")[0]
                .get_text(strip=True)
            if soup.find("div", attrs={"id": "salaryInfoAndJobType"})
            else "Not specified might be in description"
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
            "source": "indeed"
        }

        print(f"Scraped: {title}")
        return job_data

    except Exception as e:
        print(f"Failed scraping {job_url}: {e}")
        return None


def process_job_listings():

    options = Options()

    # Do NOT use old --headless (more detectable)
    #options.add_argument("--headless=new")

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

    max_pages = get_field_value(
        "V_number_of_pages",
        "Job_Scrapers/indeed/configs.json"
    )

    current_url = get_field_value(
        "start_link",
        "Job_Scrapers/indeed/configs.json"
    )

    all_new_jobs = []

    # 🔥 Load master URLs ONCE
    existing_urls = get_existing_urls("Job_Scrapers/master-input.json")

    pages_scraped = 0

    while current_url and (not max_pages or pages_scraped < max_pages):

        soup = get_soup_from_url(current_url,driver)
        write_str_to_txt_file(soup.prettify(), f"Job_Scrapers/files/page_{pages_scraped}_{int(time.time())}.txt")
        job_urls = get_job_urls_from_soup(soup)

        for job_url in job_urls:

            # 🚀 Skip before scraping
            if job_url in existing_urls:
                print(f"Skipping existing job: {job_url}")
                continue

            try:
                # Only now scrape detail page
                job_data = scrape_job_detail_page(job_url,driver)

                if job_data and job_data["job_title"] != "Not specified" and job_data["company"] != "Not specified":
                    all_new_jobs.append(job_data)
                    existing_urls.add(job_url)  # prevent duplicate in same run
                else:
                    print(f"⚠️ No data returned for: {job_url}")

            except Exception as e:
                print(f"❌ Failed scraping job details: {job_url}")
                print(f"   Reason: {e}")
                continue  # 🔥 important — move to next job

            if do_one:
                break

        current_url = get_next_from_soup(soup)
        pages_scraped += 1

    if not all_new_jobs:
        print("No new jobs found.")
        return
    
    driver.quit()

    fresh_file = create_fresh_json_file()
    print(f"Created fresh file: {fresh_file}")
    append_to_json_list(fresh_file, all_new_jobs)
    append_to_json_list("Job_Scrapers/master-input.json", all_new_jobs)
    append_to_json_list("Job_Scrapers/pending-input.json", all_new_jobs)

    print(f"Saved {len(all_new_jobs)} new jobs.")