from Interfaces.google_manager import load_token


def get_service():
    """
    Returns a Google Sheets API service object using token from load_token()
    """
    from googleapiclient.discovery import build

    creds = load_token()
    service = build('sheets', 'v4', credentials=creds)
    return service


def create_job_spreadsheet(title):
    """
    Creates a new spreadsheet and returns its spreadsheetId
    """
    try:
        service = get_service()
        spreadsheet_body = {
           "properties": {"title": title},"sheets": [
                {"properties": {"title": "Listings"}},
                {"properties": {"title": "Applications"}},
                {"properties": {"title": "Signature"}}
            ]
        } 
        
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet["spreadsheetId"]

        append_sheet(
            spreadsheet_id,
            "Listings",
            [
                "listing_id",
                "job_title",
                "company",
                "location",
                "job_location_type",
                "employment_type",
                "position",
                "pay_per_hour",
                "passed",
                "score",
                "strengths",
                "weaknesses",
                "risks",
                "reasoning_summary",
                "ai_model_used",
                "source",
                "job_url",
                "date_found",
                "time_found",
                "job_description"
            ]
        )

        append_sheet(
            spreadsheet_id,
            "Applications",
            [
                "listing_id",
                "job_title",
                "company",
                "application_status",
                "application_date",
                "application_method",
                "apply_link",
                "cv_used",
                "apply_email",
                "email_sent",
                "ai_model_used",
                "job_folder_path",
                "notes"
            ]
        )

        append_sheet(
            spreadsheet_id,
            "Signature",
            [
                "Made",
                "By",
                "Youssef Habashy"
            ]
        )

    except Exception as e:
        print(f"Error creating spreadsheet: {str(e)}")
        raise e
    return spreadsheet  # contains spreadsheetId, properties, sheets, spreadsheetUrl    

def get_sheet_id_by_name(spreadsheet, sheet_name):
    for sheet in spreadsheet["sheets"]:
        props = sheet["properties"]
        if props["title"] == sheet_name:
            return props["sheetId"]

    raise ValueError(f"Sheet '{sheet_name}' not found")

# sheets_interface2.py

def id_exists(service, spreadsheet_id: str, sheet_name: str, value: str) -> bool:
    """
    Searches for a value in the first column (A) of a given sheet.

    :param service: Google Sheets API service object
    :param spreadsheet_id: spreadsheet ID
    :param sheet_name: sheet tab name
    :param value: value to search
    :return: True if found, False otherwise
    """
    try:
        range_name = f"{sheet_name}!A:A"

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get("values", [])

        if not values:
            return False

        # Flatten column values
        column_values = [row[0] for row in values if row]

        return value in column_values

    except Exception as e:
        print(f"Error searching value in sheet: {e}")
        return False

def read_sheet(spreadsheet_id, range_name="Sheet1!A:Z"):
    """
    Reads values from a spreadsheet range.
    Returns a list of rows.
    """
    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    return result.get('values', [])

def append_sheet(spreadsheet_id, sheet_name, values):
    """
    Appends a row of values to a spreadsheet sheet.
    """
    service = get_service()
    range_name = f"{sheet_name}!A:Z"  # use sheet name here
    body = {"values": [values]}

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()
    return result


def update(spreadsheet_id, range_name, values):
    """
    Updates a range of cells with the given values.
    """
    service = get_service()
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()
    return result
