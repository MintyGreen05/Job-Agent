from pipeline import CONFIG_PATH
from Job_Scrapers.stepstone.stepstone import process_job_listings as stepstone_process_listings
from Job_Scrapers.indeed.indeed import process_job_listings as indeed_process_listings
from Job_Scrapers.Linkedin.Search import process_job_listings as linkedin_process_listings
from Job_Scrapers.helper import get_field_value

def start(source):
    if "stepstone" in source:
        stepstone_process_listings()
    if "linkedin" in source:
        linkedin_process_listings()
    if "indeed" in source:
        indeed_process_listings()
    
if __name__ == "__main__":
    
    start(get_field_value("S_scrape_mode", CONFIG_PATH))
    #indeed_process_listings()