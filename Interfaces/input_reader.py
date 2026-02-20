import json


def read_jobs_from_json(file_path):
    """
    Reads a JSON file that contains an "inputs" key.
    Returns a list of job dictionaries.
    """

    try:
        # Open and load JSON file
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Check if "inputs" exists
        if "inputs" not in data:
            print("❌ Error: 'inputs' key not found in JSON.")
            return []

        jobs = []

        # Convert each job entry into a dict
        for job in data["inputs"]:
            job_dict = dict(job)  # Explicit dict conversion
            jobs.append(job_dict)

        print(f"✅ Successfully loaded {len(jobs)} job(s) from JSON file.")
        return jobs

    except FileNotFoundError:
        print("❌ Error: File not found.")
        return []

    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format.")
        return []

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []


def job_object_to_json_text(job_object):
    """
    Converts a single job dictionary into formatted JSON text.
    Returns JSON string.
    """

    try:
        json_text = json.dumps(job_object, indent=4)

        print("✅ Successfully converted job object to JSON text.")
        return json_text

    except TypeError as e:
        print(f"❌ Error converting object to JSON: {e}")
        return ""