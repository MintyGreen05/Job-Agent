from PyPDF2 import PdfReader
import json
import hashlib
import re

def cv_to_text(path = "Files/MyCV.pdf"):
    reader = PdfReader(path)
    text = "-- CV START --\n\n"
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


import datetime

def write_log(log_file_path, message):
    """
    Appends a single log line to a text file with a timestamp.
    
    :param log_file_path: Path to the log file
    :param message: The log message to write
    """
    try:
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"

        # Open file in append mode and write the line
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(log_line)

    except Exception as e:
        print(f"❌ Failed to write log: {e}")


def get_field_value(field_name, json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    return data.get(field_name)


def set_field_value(field_name, value, json_file_path):
    """
    Updates (or adds) a field in the JSON file and saves it.
    
    :param field_name: Key to update or add
    :param value: Value to assign
    :param json_file_path: Path to the JSON file
    """
    try:
        # Read current data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update or add the field
        data[field_name] = value

        # Write back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        print(f"✅ Successfully updated '{field_name}' in JSON.")

    except FileNotFoundError:
        print("❌ Error: JSON file not found.")

    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def normalize_text(text):
    """
    Normalizes text for stable hashing:
    - Lowercases
    - Removes extra whitespace
    - Removes line breaks
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text.strip()


def generate_hash(job):
    """
    Generates a stable SHA-256 hash for a job listing.
    Uses key identifying fields including a normalized description.
    """

    try:
        # Normalize key fields
        title = normalize_text(job.get("job_title", ""))
        company = normalize_text(job.get("company", ""))
        location = normalize_text(job.get("location", ""))
        # Use only first 1500 characters of description to reduce noise
        description = normalize_text(job.get("job_description", ""))[:1500]

        combined_string = title + company + location + description

        hash = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()

        print("✅ Job hash generated successfully.")
        return hash

    except Exception as e:
        print(f"❌ Error generating job hash: {e}")
        return None

def read_json_text(json_text):
    """
    Converts AI-generated JSON text into a Python dictionary.
    """
    import json
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON text:", e)
        return {}

if __name__ == "__main__":
    print(cv_to_text())