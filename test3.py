# main.py

from Interfaces.gmail_interface import send_email
from Interfaces.helpers import get_field_value
from Interfaces.input_reader import read_jobs_from_json, job_object_to_json_text

def main():
    # Example usage
    """send_email(
        to_email="recipient@example.com",
        attachment_paths=[
            "files/myCV.pdf"
        ],
        subject="Application for Junior Developer Position",
        body_text="Dear Hiring Team,\n\nPlease find my application attached.\n\nBest regards,\nYour Name"
    )"""
    #print(get_config_value("spreadsheet_id", "Run-Configs/config.json"))

    jobs = read_jobs_from_json("Run-Configs/input.json")

    if jobs:
        json_text = job_object_to_json_text(jobs[0])
        print(json_text)

if __name__ == "__main__":
    main()