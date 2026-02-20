"""
INTEGRATION TEST FILE

If RUN_TEST = True:
    - Creates root folder
    - Creates spreadsheet
    - Moves spreadsheet to root folder
    - Creates job folder
    - Generates 3 artifacts
    - Uploads them
    - Cleans up local files
"""

RUN_TEST = True  # <---- Toggle this


# =========================
# Imports
# =========================

from Interfaces.sheets_interface import create_job_spreadsheet
from Interfaces.drive_interface import (
    create_root_folder,
    create_job_folder,
    upload_job_file,
    move_file_to_folder,
)
from Interfaces.artifact_generator import (
    generate_job_artifacts,
    cleanup_job_artifacts,
)


# =========================
# Test Configuration
# =========================

TEST_ROOT_FOLDER_NAME = "JobAgent_TEST"
TEST_SPREADSHEET_NAME = "JobAgent Main TEST"

TEST_COMPANY = "OpenAI"
TEST_JOB_TITLE = "Backend Engineer2"

TEST_COVER_LETTER = """Dear Hiring Manager,

I am excited to apply for the Backend Engineer position.
My experience in scalable systems aligns well with your needs.

Best regards,
Test User
"""

TEST_EMAIL = """Subject: Application for Backend Engineer

Hello,

Please find my application attached.

Best,
Test User
"""

TEST_MESSAGE = """Hi,

I recently applied for the Backend Engineer role and would love to connect.

Thanks!
"""


# =========================
# Main Test Logic
# =========================

def run_test():

    print("=== STARTING INTEGRATION TEST ===")

    # 1️⃣ Create root folder
    root_folder_id = create_root_folder(TEST_ROOT_FOLDER_NAME)
    print(f"Root folder created: {root_folder_id}")

    # 2️⃣ Create spreadsheet
    spreadsheet = create_job_spreadsheet(TEST_SPREADSHEET_NAME)
    spreadsheet_id = spreadsheet["spreadsheetId"]

    print(f"Spreadsheet created: {spreadsheet_id}")

    # 3️⃣ Move spreadsheet into root folder
    move_file_to_folder(spreadsheet_id, root_folder_id)
    print("Spreadsheet moved to root folder")

    # 4️⃣ Create job folder
    job_folder_id = create_job_folder(
        TEST_COMPANY,
        TEST_JOB_TITLE,
        root_folder_id
    )
    print(f"Job folder created: {job_folder_id}")

    # 5️⃣ Generate artifacts locally
    artifacts = generate_job_artifacts(
        TEST_COMPANY,
        TEST_JOB_TITLE,
        TEST_COVER_LETTER,
        TEST_EMAIL,
        TEST_MESSAGE,
    )

    print("Local artifacts generated")

    # 6️⃣ Upload artifacts
    upload_job_file(
        job_folder_id,
        artifacts["files"]["cover_letter"],
        "Cover_Letter.pdf",
        "application/pdf",
    )

    upload_job_file(
        job_folder_id,
        artifacts["files"]["email"],
        "Email.txt",
        "text/plain",
    )

    upload_job_file(
        job_folder_id,
        artifacts["files"]["message"],
        "Message.txt",
        "text/plain",
    )

    print("Artifacts uploaded successfully")

    # 7️⃣ Cleanup local temp files
    
    cleanup_job_artifacts(artifacts["job_dir"])
    print("Local artifacts cleaned up")

    print("=== TEST COMPLETED SUCCESSFULLY ===")
    


# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    if RUN_TEST:
        run_test()
    else:
        print("RUN_TEST is False. Nothing executed.")
