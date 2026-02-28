from pipeline import CONFIG_PATH
from Job_Scrapers.stepstone.stepstone import process_job_listings as stepstone_process_listings
from Job_Scrapers.indeed.indeed import process_job_listings as indeed_process_listings
from Job_Scrapers.helper import get_field_value

def start(source):
    if source == "stepstone":
        stepstone_process_listings()
    elif source == "indeed":
        indeed_process_listings()
    else:
        print(f"❌ Unknown source: {source}")

if __name__ == "__main__":
    
    start(get_field_value("S_scrape_mode", CONFIG_PATH))
    #indeed_process_listings()