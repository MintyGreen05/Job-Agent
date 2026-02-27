import json
import os
from datetime import datetime
import re

# ------------------------
# Read/write helpers
# ------------------------

def get_field_value(field_name, json_file_path):
    """Get a top-level field value from a JSON file."""
    if not os.path.exists(json_file_path):
        return None
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(field_name)

def create_fresh_json_file(prefix="jobs"):
    """
    Create a new JSON file with current datetime in filename inside a fixed folder "job_data",
    with structure {"inputs": []}.
    Returns the full path of the created file.
    """
    # Fixed folder path
    folder_path = "Job_Scrapers/files"
    
    # Make sure the folder exists
    os.makedirs(folder_path, exist_ok=True)
    
    # Timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    
    # Full path
    full_path = os.path.join(folder_path, filename)
    
    # Create the file with empty structure
    data = {"inputs": []}
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    return full_path


def append_to_json_list(json_file_path, new_entries):
    """
    Append one or more job dicts to the "inputs" array of a JSON file.
    Creates the file if it doesn't exist.
    """
    if not os.path.exists(json_file_path):
        data = {"inputs": []}
    else:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "inputs" not in data:
            data["inputs"] = []

    # Ensure new_entries is a list
    if isinstance(new_entries, dict):
        new_entries = [new_entries]

    data["inputs"].extend(new_entries)

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def remove_existing_urls_from_master(job_list, master_file_path):
    """
    Remove any jobs from job_list whose job_url already exists in master_file_path.
    Returns the filtered list.
    """
    if not os.path.exists(master_file_path):
        return job_list

    with open(master_file_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    existing_urls = {job.get("job_url") for job in master_data.get("inputs", [])}

    filtered = [job for job in job_list if job.get("job_url") not in existing_urls]

    return filtered

def write_str_to_txt_file(text, filename="output.txt"):
    """
    Creates a text file (or overwrites if it exists) and writes the provided string into it.
    
    :param text: The string content to write
    :param filename: Name or path of the text file
    :return: Full path of the file created
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Written to file: {filename}")
    return filename

def extract_and_save_preloaded_state(soup):
    script = soup.find("script", string=re.compile("window.__PRELOADED_STATE__"))

    if not script:
        print("❌ Could not find PRELOADED_STATE")
        return None

    match = re.search(
        r"window\.__PRELOADED_STATE__\s*=\s*(\{.*\})\s*;",
        script.string,
        re.DOTALL
    )

    if not match:
        print("❌ JSON extraction failed")
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stepstone_raw_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"✅ JSON saved to: {filename}")
    return filename

def get_existing_urls(master_file_path):
    """
    Load all existing job_url values from master file.
    Returns a set for O(1) lookup.
    """
    if not os.path.exists(master_file_path):
        return set()

    with open(master_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {job.get("job_url") for job in data.get("inputs", []) if job.get("job_url")}