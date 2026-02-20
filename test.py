# test_sheets_interface.py
import traceback
import Interfaces.google_manager as si

def test_all_operations():
    errors = []

    # --- 1. Test create ---
    try:
        spreadsheet = si.create("JobAgentTestSheet")
        sheet_id = spreadsheet.get("spreadsheetId")
        sheet_url = spreadsheet.get("spreadsheetUrl")
        print(f"[CREATE] Success. Spreadsheet ID: {sheet_id}, URL: {sheet_url}")
    except Exception as e:
        errors.append(f"CREATE failed: {str(e)}\n{traceback.format_exc()}")

    # --- 2. Test append ---
    try:
        si.append(sheet_id, ["Test Job", "Test Company", "https://example.com"])
        print("[APPEND] Success. Added a test row.")
    except Exception as e:
        errors.append(f"APPEND failed: {str(e)}\n{traceback.format_exc()}")

    # --- 3. Test read ---
    try:
        values = si.read(sheet_id)
        print(f"[READ] Success. First row: {values[0] if values else 'EMPTY'}")
    except Exception as e:
        errors.append(f"READ failed: {str(e)}\n{traceback.format_exc()}")

    # --- 4. Test update ---
    try:
        si.update(sheet_id, "A1:C1", [["Job Title", "Company", "Link"]])
        print("[UPDATE] Success. Header updated.")
    except Exception as e:
        errors.append(f"UPDATE failed: {str(e)}\n{traceback.format_exc()}")

    # --- Report ---
    if errors:
        print("\n--- ERRORS DETECTED ---")
        for err in errors:
            print(err)
    else:
        print("\nAll operations succeeded!")

if __name__ == "__main__":
    test_all_operations()
