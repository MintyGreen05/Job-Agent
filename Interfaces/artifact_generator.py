import os
import shutil
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime, UTC
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

    # Smaller margins (0.75 inch instead of 1 inch)
    margin = 0.75 * inch
    x = margin
    y = height - margin
    max_width = width - 2 * margin

    font_name = "Helvetica"
    font_size = 13  # slightly bigger text
    line_height = 16  # increase line spacing

    c.setFont(font_name, font_size)

    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""

        for word in words:
            test_line = f"{line} {word}" if line else word

            # Measure width using correct font and size
            if c.stringWidth(test_line, font_name, font_size) > max_width:
                c.drawString(x, y, line)
                y -= line_height

                if y < margin:
                    c.showPage()
                    c.setFont(font_name, font_size)
                    y = height - margin

                line = word
            else:
                line = test_line

        # Draw remaining text in paragraph
        if line:
            c.drawString(x, y, line)
            y -= line_height

            if y < margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin

        # Add extra spacing between paragraphs
        y -= line_height * 0.8

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
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    folder_name = f"{_safe_name(company_name)} - {_safe_name(job_title)}"
    job_dir = os.path.join(TEMP_ROOT, folder_name)

    _ensure_dir(job_dir)

    cover_letter_path = os.path.join(job_dir, f"Cover_Letter_{_safe_name(company_name)}.pdf")
    email_path = os.path.join(job_dir, f"Email_{_safe_name(company_name)}.txt")
    message_path = os.path.join(job_dir, f"Message_{_safe_name(company_name)}.txt")

    generate_cover_letter_pdf(cover_letter_text, cover_letter_path)
    generate_text_file(email_text, email_path)
    generate_text_file(message_text, message_path)

    return {
        "job_dir": job_dir,
        "files": {
            f"cover_letter_{_safe_name(company_name)}": cover_letter_path,
            f"email_{_safe_name(company_name)}": email_path,
            f"message_{_safe_name(company_name)}": message_path,
        },
    }


def cleanup_job_artifacts(job_dir):
    """
    Deletes local job artifacts AFTER successful upload.
    """
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir)


if __name__ == "__main__":
    result = generate_job_artifacts(
        company_name="Acme Corp",
        job_title="Software Engineer",
        cover_letter_text="Dear Hiring Manager,\n\n\n\nI am excited to apply for the Software Engineer position at Acme Corp. With my experience in Python and AI, I believe I would be a great fit for your team.\n\nSincerely,\nJohn Doe",
        email_text="Subject: Application for Software Engineer Position\n\nDear Hiring Manager,\n\nPlease find attached my cover letter and resume for the Software Engineer position at Acme Corp. I look forward to the opportunity to discuss how I can contribute to your team.\n\nBest regards,\nJohn Doe",
        message_text="Hi there! Just wanted to share that I've applied for the Software Engineer role at Acme Corp. Fingers crossed!",
    )
    