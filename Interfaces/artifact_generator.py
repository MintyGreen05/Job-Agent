import os
import shutil
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.lib.units import inch



TEMP_ROOT = "temp_jobs"


# -------------------------
# helpers
# -------------------------

def _safe_name(text: str) -> str:
    return "".join(c for c in text if c.isalnum() or c in (" ", "-", "_")).strip()


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


# -------------------------
# file generators
# -------------------------

def generate_cover_letter_pdf(text, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    x = 1 * inch  # 1 inch margin
    y = height - 1 * inch
    max_width = width - 2 * inch  # margin on both sides
    line_height = 14

    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            # Test if adding the next word exceeds max width
            if c.stringWidth(line + " " + word, "Helvetica", 12) > max_width:
                c.drawString(x, y, line)
                y -= line_height
                if y < 1 * inch:
                    c.showPage()
                    y = height - 1 * inch
                line = word
            else:
                if line:
                    line += " " + word
                else:
                    line = word
        # Draw last line of paragraph
        if line:
            c.drawString(x, y, line)
            y -= line_height
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch

    c.save()


def generate_text_file(text, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


# -------------------------
# main interface
# -------------------------

def generate_job_artifacts(
    company_name: str,
    job_title: str,
    cover_letter_text: str,
    email_text: str,
    message_text: str,
):
    """
    Creates local job artifacts and returns paths.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    folder_name = f"{_safe_name(company_name)} - {_safe_name(job_title)}"
    job_dir = os.path.join(TEMP_ROOT, folder_name)

    _ensure_dir(job_dir)

    cover_letter_path = os.path.join(job_dir, "Cover_Letter.pdf")
    email_path = os.path.join(job_dir, "Email.txt")
    message_path = os.path.join(job_dir, "Message.txt")

    generate_cover_letter_pdf(cover_letter_text, cover_letter_path)
    generate_text_file(email_text, email_path)
    generate_text_file(message_text, message_path)

    return {
        "job_dir": job_dir,
        "files": {
            "cover_letter": cover_letter_path,
            "email": email_path,
            "message": message_path,
        },
    }


def cleanup_job_artifacts(job_dir):
    """
    Deletes local job artifacts AFTER successful upload.
    """
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir)
