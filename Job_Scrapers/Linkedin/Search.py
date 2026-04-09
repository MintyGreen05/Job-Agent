import requests
import os

from Job_Scrapers.helper import append_to_json_list, create_fresh_json_file, get_existing_urls


def process_job_listings():
    api_key = os.environ["theirstack_api_key"]

    url = "https://api.theirstack.com/v1/jobs/search"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "include_total_results": False,
        "posted_at_max_age_days": 30,
        "job_location_or": [{"id": 2950159}],
        "job_title_or": [
            "Werkstudent IT",
            "Werkstudent Web",
            "Werkstudent Tech",
            "Werkstudent AI",
            "Student Web",
            "Werkstudent entwicklung"
        ],
        "employment_statuses_or": [
            "part_time"
        ],
        "url_domain_or": ["linkedin.com"],
        "page": 0,
        "limit": 25,
        "blur_company_data": False
    }

    response = requests.post(url, headers=headers, json=data)

    response_json = response.json()
    existing_urls = get_existing_urls("Job_Scrapers/master-input.json")

    all_new_jobs = []

    for job in response_json.get("data", []):
        
        job_url = job.get("final_url") or job.get("url")
        
        # Skip invalid URLs
        if not job_url:
            continue

        # Skip duplicates
        if job_url in existing_urls:
            continue

        # -------- Extract fields --------
        job_data = {
            "job_title": job.get("job_title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "job_url": job_url,
            "job_description": job.get("description"),
            "job_location_type": (
                "remote" if job.get("remote")
                else "hybrid" if job.get("hybrid")
                else "onsite"
            ),
            "employment_type": (
                ", ".join(job.get("employment_statuses"))
                if job.get("employment_statuses")
                else "not specified"
            ),
            "position": "Werkstudent",
            "pay_per_hour": "not specified",
            "source": "theirstack-linkedin"
        }

        # -------- Store --------
        all_new_jobs.append(job_data)
        existing_urls.add(job_url)


    # -------- Save --------
    if not all_new_jobs:
        print("No new jobs found.")
    else:
        fresh_file = create_fresh_json_file()
        print(f"Created fresh file: {fresh_file}")

        append_to_json_list(fresh_file, all_new_jobs)
        append_to_json_list(
    "Job_Scrapers/master-input.json",
    [
        {"job_url": job["job_url"], "job_title": job["job_title"]}
        for job in all_new_jobs
    ]
)
        append_to_json_list("Job_Scrapers/pending-input.json", all_new_jobs)

        print(f"Saved {len(all_new_jobs)} new jobs.")

