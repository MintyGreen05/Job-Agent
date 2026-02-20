# drive_interface.py
from Interfaces.google_manager import load_token


def get_service():
    """
    Returns a Google Drive API service object using token from load_token()
    """
    from googleapiclient.discovery import build

    creds = load_token()
    return build("drive", "v3", credentials=creds)


# =========================
# Root / Project Folder
# =========================

def create_root_folder(folder_name):
    """
    Creates the root Drive folder for the project.
    Returns folder_id.
    """
    try:
        service = get_service()

        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }

        folder = service.files().create(
            body=metadata,
            fields="id,name"
        ).execute()

        return folder["id"]

    except Exception as e:
        print(f"Error creating root folder '{folder_name}': {str(e)}")
        raise e


def get_folder_by_name(folder_name, parent_id=None):
    """
    Fetches a folder by name (optionally under a parent).
    Returns folder_id or None.
    """
    service = get_service()

    query = [
        "mimeType='application/vnd.google-apps.folder'",
        f"name='{folder_name}'",
        "trashed=false"
    ]

    if parent_id:
        query.append(f"'{parent_id}' in parents")

    result = service.files().list(
        q=" and ".join(query),
        fields="files(id,name)",
        pageSize=1
    ).execute()

    files = result.get("files", [])
    return files[0]["id"] if files else None


# =========================
# Job Folder
# =========================

def create_job_folder(company, job_title, root_folder_id):
    """
    Creates a job-specific folder named:
    '{Company} - {Job Title}'

    Returns folder_id and webViewLink.
    """
    try:
        service = get_service()

        folder_name = f"{company} - {job_title}"

        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [root_folder_id]
        }

        folder = service.files().create(
            body=metadata,
            fields="id,name,webViewLink"  # ← include webViewLink
        ).execute()

        return folder["id"], folder["webViewLink"]

    except Exception as e:
        print(
            f"Error creating job folder '{company} - {job_title}': {str(e)}"
        )
        raise e


def get_or_create_job_folder(company, job_title, root_folder_id):
    """
    Idempotent job folder creation.
    Returns folder_id.
    """
    folder_name = f"{company} - {job_title}"
    existing_id = get_folder_by_name(folder_name, root_folder_id)

    if existing_id:
        return existing_id

    return create_job_folder(company, job_title, root_folder_id)


# =========================
# File Uploads and Downloads and Movements
# =========================

def upload_job_file(
    job_folder_id,
    local_file_path,
    drive_file_name,
    mime_type
):
    """
    Uploads a file into a job folder.
    Returns file_id.
    """
    from googleapiclient.http import MediaFileUpload

    try:
        service = get_service()

        metadata = {
            "name": drive_file_name,
            "parents": [job_folder_id]
        }

        media = MediaFileUpload(
            local_file_path,
            mimetype=mime_type,
            resumable=True
        )

        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id,name"
        ).execute()

        return file["id"]

    except Exception as e:
        print(
            f"Error uploading '{drive_file_name}' "
            f"to folder {job_folder_id}: {str(e)}"
        )
        raise e

def Download_file(file_id, destination_path):
    """
    Downloads a file from Google Drive by file_id
    and saves it to destination_path.
    """
    from googleapiclient.http import MediaIoBaseDownload
    import io
    import os

    try:
        service = get_service()

        request = service.files().get_media(fileId=file_id)

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        fh = io.FileIO(destination_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(
                    f"Downloading {int(status.progress() * 100)}%"
                )

        fh.close()
        return destination_path

    except Exception as e:
        print(f"Error fetching file {file_id}: {str(e)}")
        raise e
    
def move_file_to_folder(file_id, folder_id):
    """
    Moves a file into a Drive folder.
    """
    service = get_service()

    # Get current parents
    file = service.files().get(
        fileId=file_id,
        fields="parents"
    ).execute()

    previous_parents = ",".join(file.get("parents", []))

    service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields="id, parents"
    ).execute()

# =========================
# Read / Debug Helpers
# =========================

def list_job_files(job_folder_id):
    """
    Lists all files inside a job folder.
    """
    service = get_service()

    result = service.files().list(
        q=f"'{job_folder_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)"
    ).execute()

    return result.get("files", [])


def delete_file(file_id):
    """
    Deletes a file or folder by ID.
    """
    service = get_service()
    service.files().delete(fileId=file_id).execute()
