import os
import shutil
import subprocess
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime, UTC
from reportlab.lib.units import inch
from Interfaces.helpers import cv_to_text, remove_from_input_by_url, write_log, generate_hash, read_json_text, get_field_value, set_field_value



TEMP_ROOT = "temp_jobs"

# Toggle resume PDF generation on/off. Override via env var:
#   RESUME_GENERATION_ENABLED=false
ENABLE_RESUME_GENERATION =   get_field_value("B_CV_tailor", "Run-Configs/config.json")




# -------------------------
# helpers
# -------------------------

def _safe_name(text: str) -> str:
    return "".join(
        c for c in text
        if c.isalnum() or c in ("-", "_")
    )


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _job_dir_for(company_name: str, job_title: str) -> str:
    folder_name = f"{_safe_name(company_name)} - {_safe_name(job_title)}"
    job_dir = os.path.join(TEMP_ROOT, folder_name)
    _ensure_dir(job_dir)
    return job_dir


# -------------------------
# file generators
# -------------------------

def generate_resume_pdf(company_name: str, job_title: str, tex_content: str, job_dir: str = None):
    if job_dir is None:
        job_dir = _job_dir_for(company_name, job_title)
    else:
        _ensure_dir(job_dir)

    safe_company = _safe_name(company_name)
    base_name = f"Resume_{safe_company}"

    tex_path = os.path.join(job_dir, f"{base_name}.tex")
    pdf_path = os.path.join(job_dir, f"{base_name}.pdf")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)
    print(f"Wrote tex file: {tex_path}")

    print("Compiling PDF with pdflatex...")
    for _ in range(2):
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={job_dir}",
                tex_path,
            ],
            capture_output=True,
            text=True,
        )

    if not os.path.exists(pdf_path):
        print("PDF compilation failed")
        raise RuntimeError(
            f"pdflatex failed to produce a PDF for {safe_company}.\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    print(f"PDF compiled: {pdf_path}")

    for ext in (".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"):
        junk_path = os.path.join(job_dir, f"{base_name}{ext}")
        if os.path.exists(junk_path):
            os.remove(junk_path)
    print("Cleaned up auxiliary LaTeX files")

    return {
        "job_dir": job_dir,
        "files": {
            f"resume_pdf_{safe_company}": pdf_path,
            f"resume_tex_{safe_company}": tex_path,
        },
    }


def generate_cover_letter_pdf(text, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    margin = 0.75 * inch
    x = margin
    y = height - margin
    max_width = width - 2 * margin

    font_name = "Helvetica"
    font_size = 14
    line_height = 18

    c.setFont(font_name, font_size)

    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""

        for word in words:
            test_line = f"{line} {word}" if line else word

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

        if line:
            c.drawString(x, y, line)
            y -= line_height

            if y < margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin

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
    job_dir: str = None,
):
    """
    Creates local job artifacts and returns paths.
    """
    if job_dir is None:
        job_dir = _job_dir_for(company_name, job_title)
    else:
        _ensure_dir(job_dir)

    safe_company = _safe_name(company_name)

    cover_letter_path = os.path.join(job_dir, f"Cover_Letter_{safe_company}.pdf")
    email_path = os.path.join(job_dir, f"Email_{safe_company}.txt")
    message_path = os.path.join(job_dir, f"Message_{safe_company}.txt")

    generate_cover_letter_pdf(cover_letter_text, cover_letter_path)
    generate_text_file(email_text, email_path)
    generate_text_file(message_text, message_path)

    return {
        "job_dir": job_dir,
        "files": {
            f"cover_letter_{safe_company}": cover_letter_path,
            f"email_{safe_company}": email_path,
            f"message_{safe_company}": message_path,
        },
    }


def cleanup_job_artifacts(job_dir):
    """
    Deletes local job artifacts AFTER successful upload.
    """
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir)