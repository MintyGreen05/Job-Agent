# pipeline.py

import datetime
import json
from Interfaces.sheets_interface import append_sheet, read_sheet, update, get_sheet_id_by_name, get_service
from Interfaces.drive_interface import create_root_folder, create_job_folder, upload_job_file, move_file_to_folder
from Interfaces.artifact_generator import generate_job_artifacts, cleanup_job_artifacts
from Interfaces.ai_client import call_ai
from Interfaces.helpers import cv_to_text, remove_from_input_by_url, write_log, generate_hash, read_json_text, get_field_value, set_field_value
from Interfaces.input_reader import read_jobs_from_json, job_object_to_json_text

CONFIG_PATH = "Run-Configs/config.json"
LOG_FILE = "Files/logs.txt"
if get_field_value("B_read_manual_input_mode", CONFIG_PATH):
    INPUT_JSON_PATH = "Run-Configs/input.json"
else:
    INPUT_JSON_PATH = "Job-Scrapers/pending-input.json"
EVALUATION_PATH = get_field_value("use_evaluation", CONFIG_PATH) or "Run-Configs/evaluation-prompt.json"
GENERATION_PATH = get_field_value("use_generation", CONFIG_PATH) or "Run-Configs/generation-prompt.json"
ROOT_FOLDER_NAME = "JobAgent"
LISTINGS_SHEET_NAME = "Listings"
APPLICATIONS_SHEET_NAME = "Applications"

# ---------------------------
# Step 1: Initialize Project
# ---------------------------

def initialize_project():
    """
    Initializes project by checking config:
    - If initialized: return spreadsheet_id
    - Else: create root folder, spreadsheet, job folder, store IDs in config
    """
    initialized = get_field_value("initialized", CONFIG_PATH)
    if initialized and get_field_value("B_always_initialize", CONFIG_PATH) == False:
        spreadsheet_id = get_field_value("spreadsheet_id", CONFIG_PATH)
        root_folder_id = get_field_value("root_folder_id", CONFIG_PATH)
        write_log(LOG_FILE, "Project already initialized. Proceeding...")
        print("✅ Project already initialized.")
        return spreadsheet_id, root_folder_id
    else:
        write_log(LOG_FILE, "Initializing project...")
        print("⚡ Initializing project...")

        # 1️⃣ Create root folder in Drive
        root_folder_id = create_root_folder(ROOT_FOLDER_NAME)
        print(f"Root folder created: {root_folder_id}")
        write_log(LOG_FILE, f"Root folder created: {root_folder_id}")

        # 2️⃣ Create Spreadsheet
        from Interfaces.sheets_interface import create_job_spreadsheet
        spreadsheet = create_job_spreadsheet("JobAgent Main")
        spreadsheet_id = spreadsheet["spreadsheetId"]
        print(f"Spreadsheet created: {spreadsheet_id}")
        write_log(LOG_FILE, f"Spreadsheet created: {spreadsheet_id}")

        # 3️⃣ Move spreadsheet to root folder
        move_file_to_folder(spreadsheet_id, root_folder_id)
        print("Spreadsheet moved to root folder")
        write_log(LOG_FILE, "Spreadsheet moved to root folder")

        # 4️⃣ Update config
        set_field_value("spreadsheet_id", spreadsheet_id, CONFIG_PATH)
        set_field_value("root_folder_id", root_folder_id, CONFIG_PATH)
        set_field_value("initialized", True, CONFIG_PATH)

        return spreadsheet_id, root_folder_id

# ---------------------------
# Step 2: Read Jobs
# ---------------------------

def read_jobs():
    """
    Reads job inputs from Listings sheet.
    Returns a list of job dictionaries.
    """
    write_log(LOG_FILE, "Reading job inputs...")
    print("📥 Reading job inputs...")

    jobs = read_jobs_from_json(INPUT_JSON_PATH)

    write_log(LOG_FILE, f"Read {len(jobs)} jobs from sheet.")
    print(f"✅ Read {len(jobs)} jobs.")
    return jobs

# ---------------------------
# Step 3: Process Jobs
# ---------------------------

def process_jobs(jobs, spreadsheet_id, root_folder_id, cv_text):
    """
    Processes each job:
    - Hash for ID
    - Skip if already in sheet
    - Evaluate via AI
    - Append evaluation to Listings
    - Generate artifacts if evaluation passes
    """
    applications_made = 0

    for job in jobs:
        print("\n---------------------------\n")
        # Generate unique hash
        job_id = generate_hash(job)
        job["job_hash"] = job_id
        write_log(LOG_FILE, f"Processing job: {job['job_title']} @ {job['company']} (hash: {job_id})")
        print(f"🔹 Processing job: {job['job_title']} @ {job['company']}")

        # Check if job hash exists in Listings
        from Interfaces.sheets_interface import id_exists
        if id_exists(get_service(), spreadsheet_id, LISTINGS_SHEET_NAME, job_id):
            write_log(LOG_FILE, f"Job {job_id} already exists. Skipping...")
            print("⚠️ Job already exists. Skipping.")
            continue

        # Assign date and time found
        now = datetime.datetime.now()
        job["date_found"] = now.strftime("%Y-%m-%d")
        job["time_found"] = now.strftime("%H:%M:%S")

        # ---------------------------
        # AI Evaluation
        # ---------------------------
        eval_prompt = job_object_to_json_text(job) 
        write_log(LOG_FILE, "Sending job to AI for evaluation")
        print("🤖 Evaluating job via AI...")

        if get_field_value("B_dummy_evaluation_ai", CONFIG_PATH):
            evaluation_json_text = """
                        {"score": 82,
            "strengths": [
                "Role is located in central Berlin with hybrid flexibility",
                "Position is explicitly junior-level and student-friendly",
                "Core technologies (Python, REST APIs, SQL) match user requirements",
                "Part-time workload (20 hours per week) aligns with constraints",
                "Compensation is clearly stated and paid"
            ],
            "weaknesses": [
                "Limited exposure to cloud infrastructure mentioned",
                "Frontend technologies are not part of the stack"
            ],
            "risks": [
                "Company is an early-stage startup with potential stability concerns",
                "Tech stack includes a niche framework that may limit transferability"
            ],
            "reasoning_summary": "The position satisfies all major hard constraints including location in Berlin, junior seniority, part-time workload, and paid compensation. The technical stack aligns well with the user's core software engineering focus, particularly in backend development. Minor weaknesses exist in limited cloud exposure and niche tooling. Overall, this represents a strong strategic fit with manageable risks.",
            "email": "jobs@techstartup-berlin.de"
            }"""
            ai_model_used1 = "Dummy Eval Model"
        else:
            evaluation_json_text, ai_model_used1 = call_ai(
                description=eval_prompt,
                prompt=get_field_value("prompt", EVALUATION_PATH),
                additional = get_field_value("requirements", EVALUATION_PATH),
                additional2 = cv_text
            )
        #print(evaluation_json_text)
        evaluation_json = read_json_text(evaluation_json_text)
        job.update(evaluation_json)

        # ---------------------------
        # Append evaluation to Listings sheet
        # ---------------------------
        append_values = [
            job_id,
            job.get("job_title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("job_location_type", ""),
            job.get("employment_type", ""),
            job.get("position", ""),
            job.get("pay_per_hour", ""),
            "passed" if job.get("score", 0) >= 70 else "failed",
            job.get("score", ""),
            json.dumps(job.get("strengths", [])),
            json.dumps(job.get("weaknesses", [])),
            json.dumps(job.get("risks", [])),
            job.get("reasoning_summary", ""),
            ai_model_used1,
            job.get("source", ""),
            job.get("job_url", ""),
            job["date_found"],
            job["time_found"],
            job.get("job_description", "")
        ]
        append_sheet(spreadsheet_id, LISTINGS_SHEET_NAME, append_values)
        write_log(LOG_FILE, f"Job appended to sheet: {job_id}")
        print(f"✅ Job appended to Listings sheet.")

        # ---------------------------
        # Generate Artifacts if evaluation passed
        # ---------------------------
        if get_field_value("B_apply", CONFIG_PATH):
            if job.get("score", 0) >= get_field_value("V_min_score", CONFIG_PATH):
                write_log(LOG_FILE, f"Job {job_id} passed evaluation.")
                print(f"passed evaluation {job['job_title']}...")
                write_log(LOG_FILE, f"Generating artifacts for job {job_id}")
                print(f"✍️ Generating artifacts for job {job['job_title']}...")

                 # Use call_ai to generate message, email, and cover letter

                if get_field_value("B_dummy_generation_ai", CONFIG_PATH):
                    artifact_json_text = """
                    {
                    "message": "Hello, I recently came across your Junior Software Engineer position in Berlin and was immediately interested. With hands-on experience in Python backend development and REST API design, I believe my technical background aligns well with your current needs. I would welcome the opportunity to contribute and learn more about your engineering team.",
                    "email_subject": "Application for Junior Software Engineer - Berlin",
                    "email": "Dear Hiring Team,\\n\\nI am writing to express my interest in the Junior Software Engineer position based in Berlin. With practical experience in Python development, API integration, and database management, I am confident in my ability to contribute effectively to your team.\\n\\nThrough academic and project-based experience, I have built and deployed backend systems, worked with SQL databases, and collaborated in agile environments. I am particularly drawn to your company's focus on scalable backend systems and innovative product development.\\n\\nI would greatly appreciate the opportunity to further discuss how my background aligns with your needs and how I can contribute to your team. I look forward to your response.\\n\\nKind regards,\\nMax Mustermann",
                    "cover_letter": "Max Mustermann\\nBerlin, Germany\\n\\nDear Hiring Team,\\n\\nI am excited to apply for the Junior Software Engineer position in Berlin. The role strongly aligns with my academic background in Computer Science and my hands-on experience building backend applications using Python and RESTful APIs.\\n\\nDuring my academic projects and practical work, I developed backend services, implemented database schemas using SQL, and contributed to collaborative software development in agile teams. I focused on writing clean, maintainable code and ensuring reliable system performance.\\n\\nIn previous projects, I took ownership of backend modules that improved data processing efficiency and reduced response times. I consistently prioritize writing structured, scalable code while maintaining strong collaboration with team members.\\n\\nI am eager to bring my technical skills, motivation, and problem-solving mindset to your engineering team. I would welcome the opportunity to discuss how I can contribute to your continued success.\\n\\nSincerely,\\nMax Mustermann"
                    }
                    """
                    ai_model_used2 = "Dummy Gen Model"
                else:
                    artifact_json_text, ai_model_used2 = call_ai(
                        prompt=get_field_value("prompt", GENERATION_PATH),
                        description=job_object_to_json_text(job), 
                        additional = cv_text,
                        additional2="")

                artifact_json = read_json_text(artifact_json_text)

                # Ensure email has subject at start
                email_text = f"Subject: {artifact_json.get('email_subject','')}\n\n{artifact_json.get('email','')}"

                # Generate local files
                artifacts = generate_job_artifacts(
                    company_name=job["company"],
                    job_title=job["job_title"],
                    cover_letter_text=artifact_json.get("cover_letter", ""),
                    email_text=email_text,
                    message_text=artifact_json.get("message", "")
                )

                # Create or get job folder in Drive
                job_folder_id, job_folder_url = create_job_folder(job["company"], job["job_title"], root_folder_id)
                write_log(LOG_FILE, f"Job folder ready: {job_folder_id}")

                # Upload artifacts
                for name, path in artifacts["files"].items():
                    mimetype = "application/pdf" if name == "cover_letter" else "text/plain"
                    upload_job_file(job_folder_id, path, f"{name}.{'pdf' if name=='cover_letter' else 'txt'}", mimetype)

                

                email_sent = False
                if get_field_value("B_apply_email", CONFIG_PATH) and (job["email"] != "N/A" and job["email"] != ""):
                    write_log(LOG_FILE, f"Sending application email for job {job_id}")
                    print("📧 Sending application email...")
                    from Interfaces.gmail_interface import send_email
                    send_email(
                        to_email=job["email"],
                        attachment_paths=[get_field_value("use_cv", CONFIG_PATH),artifacts["files"].get("cover_letter", "")],
                        subject=artifact_json.get("email_subject"),
                        body_text=artifact_json.get("email")
                    )
                    email_sent = True
                    write_log(LOG_FILE, f"Application email sent for job {job_id}")
                    print("✅ Application email sent.")
                
                # Cleanup local artifacts
                if get_field_value("B_clean_up",CONFIG_PATH):
                    cleanup_job_artifacts(artifacts["job_dir"])
                    write_log(LOG_FILE, f"Artifacts uploaded and local files cleaned for job {job_id}")
                    print("✅ Artifacts uploaded and local files cleaned.")
                else:
                    write_log(LOG_FILE, f"Artifacts uploaded for job {job_id}")
                    print("✅ Artifacts uploaded.")

                # ---------------------------
                # Append to Applications sheet
                # ---------------------------
                app_values = [
                    job_id,
                    job.get("job_title", ""),
                    job.get("company", ""),
                    "waiting_manual_input",
                    job["date_found"],
                    "AI Generated",
                    job.get("job_url", ""),
                    get_field_value("use_cv", CONFIG_PATH),
                    job.get("email", "N/A"),
                    email_sent,
                    ai_model_used2,
                    job_folder_url,
                    ""
                ]
                append_sheet(spreadsheet_id, APPLICATIONS_SHEET_NAME, app_values)
                write_log(LOG_FILE, f"Application entry appended for job {job_id}")
                print(f"📄 Application entry appended to Applications sheet.")
                applications_made += 1 
                if applications_made>=get_field_value("V_max_applications_per_run", CONFIG_PATH):
                    write_log(LOG_FILE, f"Maximum applications per run reached. Stopping further applications.")
                    print("⚠️ Maximum applications per run reached. Stopping further applications.")
                    break
                if get_field_value("B_input_file_culling", CONFIG_PATH):
                    write_log(LOG_FILE, f"culling from input folder {job['job_url']}")
                    remove_from_input_by_url(job["job_url"], INPUT_JSON_PATH)
            else:
                write_log(LOG_FILE, f"Job {job_id} failed evaluation, skipping artifact generation.")
                print(f"⚠️ Job {job['job_title']} failed evaluation. Skipping artifacts.")
# ---------------------------
# Step 4: Main Pipeline
# ---------------------------

def main_pipeline():
    write_log(LOG_FILE, "=== Starting Job Pipeline ===")
    print("🚀 Starting Job Pipeline...")

    spreadsheet_id, root_folder_id = initialize_project()
    jobs = read_jobs()
    cv_text = cv_to_text(get_field_value("use_cv", CONFIG_PATH))

    process_jobs(jobs, spreadsheet_id, root_folder_id, cv_text)

    write_log(LOG_FILE, "=== Pipeline Complete ===")
    print("🎉 Pipeline Complete.")

# ---------------------------
# Entry Point
# ---------------------------

if __name__ == "__main__":
    main_pipeline()