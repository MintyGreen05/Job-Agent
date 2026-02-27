from stepstone.stepstone import process_job_listings as stepstone_process_listings
from indeed.indeed import process_job_listings as indeed_process_listings

def start(source):
    if source == "stepstone":
        stepstone_process_listings()
    elif source == "indeed":
        indeed_process_listings()
    else:
        print(f"❌ Unknown source: {source}")

if __name__ == "__main__":
    stepstone_process_listings()
    #indeed_process_listings()