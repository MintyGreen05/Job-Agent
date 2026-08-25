import json
import re
from Interfaces.ai_client import call_ai
from Interfaces.input_reader import read_jobs_from_json, job_object_to_json_text



# ---------------------------------------------------------------------------
# 1. Generate the project entry via the AI
# ---------------------------------------------------------------------------
def generate_project_entry(job, cv_text, use_generation_prompt, preferred_model="gemini-3-flash-preview"):
    """
    Calls the AI with the resume-project-generation prompt, the job description,
    and the user's CV text as additional context.

    Returns the raw AI response string (still possibly wrapped in ``` fences).
    """
    ai_result, ai_model_used = call_ai(
        prompt=use_generation_prompt,
        description=job_object_to_json_text(job),
        additional=cv_text,
        additional2="",
        preferred_model=preferred_model
    )
    return ai_result, ai_model_used


# ---------------------------------------------------------------------------
# 2. Strip markdown code fences (```json ... ```) if present
# ---------------------------------------------------------------------------
def strip_code_fences(ai_result):
    """
    Removes leading/trailing markdown code fences from an AI response,
    e.g. ```json ... ``` or ``` ... ```.
    """
    ai_result = ai_result.strip()
    if ai_result.startswith("```"):
        # Remove first line (```json or ```)
        ai_result = ai_result.split('\n', 1)[1]
        # Remove last line (```)
        ai_result = ai_result.rsplit('\n', 1)[0]
    return ai_result.strip()


# ---------------------------------------------------------------------------
# 3. Parse the cleaned JSON into a dict
# ---------------------------------------------------------------------------
def parse_project_json(ai_result):
    """
    Cleans and parses the AI's JSON response into a Python dict.
    Expected schema:
    {
        "project_name": "string",
        "tech_stack": "string",
        "bullets": ["string", "string"]
    }
    """
    cleaned = strip_code_fences(ai_result)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}\nRaw response:\n{ai_result}")

    required_keys = ("project_name", "tech_stack", "bullets")
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key '{key}' in AI response: {data}")

    if not isinstance(data["bullets"], list) or len(data["bullets"]) < 2:
        raise ValueError(f"'bullets' must be a list with at least 2 items: {data}")

    return data

def escape_latex(text):
    """
    Escapes LaTeX special characters so AI-generated text can't break compilation.
    """
    # Protect backslashes first using a placeholder, so the braces we
    # introduce for \textbackslash{} don't get re-escaped by the { and }
    # rules below.
    BACKSLASH_PLACEHOLDER = "\x00"
    text = text.replace("\\", BACKSLASH_PLACEHOLDER)

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Now substitute the real backslash command, after all other escaping is done
    text = text.replace(BACKSLASH_PLACEHOLDER, r"\textbackslash{}")
    return text
# ---------------------------------------------------------------------------
# 4. Populate the LaTeX \resumeProjectHeading block
# ---------------------------------------------------------------------------
def build_resume_project_block(project_data, date="July 2026"):
    """
    Takes the parsed project JSON (project_name, tech_stack, bullets)
    and returns the filled-in LaTeX \resumeProjectHeading string,
    preserving indentation and line structure of the original template.
    """
    project_name = escape_latex(project_data["project_name"])
    tech_stack = escape_latex(project_data["tech_stack"])
    escaped_bullets = []
    
    for bullet in project_data["bullets"]:
        # Append each escaped string to our new list
        escaped_bullets.append(escape_latex(bullet))

    # Grab the first two bullet points from the list
    bullet_one = escaped_bullets[0] if len(escaped_bullets) > 0 else ""
    bullet_two = escaped_bullets[1] if len(escaped_bullets) > 1 else ""

    latex_block = (
        "\\resumeProjectHeading\n"
        "        {\\textbf{" + project_name + "} $|$ \\emph{" + tech_stack + "}}{" + date + "}\n"
        "        \\resumeItemListStart\n"
        "          \\resumeItem{" + bullet_one + "}\n"
        "          \\resumeItem{" + bullet_two + "}\n"
        "        \\resumeItemListEnd\n"
        "        \\vspace{-11pt}"
    )
    return latex_block


# ---------------------------------------------------------------------------
# 5. Insert the built block into a file at the "[Placeholder]" marker
# ---------------------------------------------------------------------------
def insert_into_file(latex_block, file_path, marker="%[Placeholder]", output_path=None):
    """
    Reads the file at file_path, replaces the first occurrence of `marker`
    with latex_block, and writes the result either back to file_path or
    to output_path if provided.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        file_text = f.read()

    if marker not in file_text:
        raise ValueError(f"Marker '{marker}' not found in file: {file_path}")

    updated_text = file_text.replace(marker, latex_block, 1)

    target_path = output_path if output_path else file_path
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(updated_text)

    return target_path


# ---------------------------------------------------------------------------
# End-to-end orchestration
# ---------------------------------------------------------------------------
def generate_and_insert_project(job, cv_text, use_generation_prompt, file_path,
                                 date="August 2026", marker="%[Placeholder]",
                                 output_path=None, preferred_model="gemini-3-flash-preview"):
    print("Calling AI to generate project entry...")
    ai_result, ai_model_used = generate_project_entry(
        job, cv_text, use_generation_prompt, preferred_model
    )
    print(f"AI response received (model used: {ai_model_used})")

    project_data = parse_project_json(ai_result)
    print(f"Parsed project: {project_data.get('project_name')}")

    latex_block = build_resume_project_block(project_data, date=date)
    print("Built LaTeX project block")

    target_path = insert_into_file(latex_block, file_path, marker=marker, output_path=output_path)
    print(f"Inserted project block into: {target_path}")

    return target_path, ai_model_used