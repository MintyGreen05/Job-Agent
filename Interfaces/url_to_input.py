#!/usr/bin/env python3
"""
visible_text_to_json.py

Usage:
- Put URLs (one per line) in 'urls.txt'
- Run: python visible_text_to_json.py
- Processed URLs are removed from urls.txt on success
- Output is appended into 'output.json' with top-level {"input": [ ... ]}

Dependencies:
pip install selenium webdriver-manager
(If you integrate OpenAI or another AI, install any extra packages needed)
"""

import json
import os
import time
import traceback
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from Interfaces.ai_client import call_ai

# -----------------------
# CONFIG
# -----------------------
URLS_FILE = "Run-Configs/urls.txt"
OUTPUT_FILE = "Run-Configs/input.json"
HEADLESS = False         # set False for visible browser for debugging
PAGE_LOAD_WAIT = 2      # seconds to wait after .get() (increase if slow sites)
SCROLL_PAUSE = 1        # pause between scrolls
MAX_SCROLLS = 6         # how many times to scroll to try to load lazy content

prompt = """You are an information extraction system.

Your task is to read the provided job-related text and extract structured information into the following JSON format.

JSON structure (always return this exact structure):

{
    "job_title": "Not specified might be in description",
    "company": "Not specified might be in description",
    "location": "Not specified might be in description",
    "job_url": "Not specified might be in description",
    "job_description": "Not specified might be in description",
    "job_location_type": "Not specified might be in description",
    "employment_type": "Not specified might be in description",
    "position": "Not specified might be in description",
    "pay_per_hour": "Not specified might be in description",
    "source": "url-scrapped"
}

Rules:
1. Extract information only from the provided text.
2. Replace the value "Not specified might be in description" only when the information is clearly present.
3. If the information cannot be confidently determined, leave the default value unchanged.
4. Always return valid JSON.
5. Do not add extra fields.
6. Do not include explanations or text outside the JSON.
7. extract the specific job description from the input, and place it inside "job_description".
8. the job URL will be at the start of the input, place it in "job_url", and it must be only in text format and not a href link.
9. If a salary per hour is mentioned, extract only the hourly pay value into "pay_per_hour".
10. The field "position" should represent the role category (e.g., Internship, Working Student, Full-time, Part-time, Student Job).
11. The field "employment_type" should represent the type of employment (e.g., part-time, full-time).
12. The field "job_location_type" should represent the location type (e.g., remote, on-site, hybrid).
13. The fields "job_title", "company", "location", "job_url", "job_description" must be filled in the output.

Output requirements:
- Preserve paragraphs and bullet points in the job description exactly as they appear.
- Do NOT summarize responsibilities, qualifications, or overview text.
- Return ONLY the JSON object.
- Keep the exact same keys and order.
- Do not include markdown formatting.

Input after this line:

"""
# -----------------------

def read_urls(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    # keep non-empty lines and ignore comments that start with #
    return [l for l in lines if l and not l.startswith("#")]

def write_urls(path: str, urls: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u.strip() + "\n")

def ensure_output_file(path: str) -> None:
    if not os.path.exists(path):
        # initialize with "inputs" array
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"inputs": []}, f, ensure_ascii=False, indent=2)

def append_to_output(path: str, obj: Dict[str, Any]) -> None:
    ensure_output_file(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # ensure "inputs" exists and is a list
    if "inputs" not in data or not isinstance(data["inputs"], list):
        data["inputs"] = []

    # if obj is a list of jobs, extend the array, else append single dict
    if isinstance(obj, list):
        data["inputs"].extend(obj)
    else:
        data["inputs"].append(obj)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def setup_driver(headless: bool = False) -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        # newer chrome may need "--headless=new"; try both if one doesn't work
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-minimized")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,800")
    # optional: avoid loading images (speeds up) - uncomment if desired:
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_visible_text_from_url(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)
    # basic wait for JS to run; increase if needed
    time.sleep(PAGE_LOAD_WAIT)

    # Scroll gradually to load lazy content
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # return exactly the visible text a user would see
    text = driver.execute_script("return document.body.innerText")
    if text is None:
        text = ""
    return text


# -----------------------
# Main pipeline
# -----------------------
def main():
    urls = read_urls(URLS_FILE)
    if not urls:
        print(f"No URLs found in {URLS_FILE}. Add one URL per line and run again.")
        return

    ensure_output_file(OUTPUT_FILE)

    
    try:
        remaining_urls = list(urls)  # will mutate when a URL succeeds
        for url in list(urls):  # iterate over original snapshot
            print(f"\nProcessing: {url}")
            try:
                driver = setup_driver(HEADLESS)
                text = get_visible_text_from_url(driver, url)
                driver.quit()
                # per your spec: url appended to the text at the start
                combined = f"{url}\n\n{text}"

                ai_result,ai_model = call_ai(combined, prompt, "","",preferred_model="gemini-2.5-flash")
                print(ai_result)

                if isinstance(ai_result, str):
                    try:
                        ai_result = json.loads(ai_result)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"AI did not return valid JSON: {e}")

                if not isinstance(ai_result, dict):
                    raise ValueError("AI did not return a JSON/dict object.")

                # append to output json
                append_to_output(OUTPUT_FILE, ai_result)
                print(f"Appended AI result for {url} to {OUTPUT_FILE}")

                # remove this url from remaining_urls and write file
                if url in remaining_urls:
                    remaining_urls.remove(url)
                    write_urls(URLS_FILE, remaining_urls)
                    print(f"Removed {url} from {URLS_FILE}")
                else:
                    # fallback safety: rewrite remaining_urls anyway
                    write_urls(URLS_FILE, remaining_urls)

            except Exception as e:
                print(f"Failed to process {url}: {e}")
                traceback.print_exc()
                # do NOT remove URL on failure; move to next
    except Exception as e:
        print(f"Unexpected error in main loop: {e}")
        traceback.print_exc()   

    print("\nDone.")

if __name__ == "__main__":
    main()