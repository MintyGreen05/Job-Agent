from stepstone.stepstone import process_job_listings as stepstone_process_listings
from indeed.indeed import process_job_listings as indeed_process_listings

if __name__ == "__main__":
    stepstone_process_listings()
    #indeed_process_listings()