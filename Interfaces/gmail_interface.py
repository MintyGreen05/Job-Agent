# gmail_interface.py

import base64
import os
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from Interfaces.google_manager import load_token


# -----------------------
# Gmail API Service
# -----------------------
def get_gmail_service():
    """
    Returns a Gmail API service object using existing token.
    """
    creds = load_token()
    return build("gmail", "v1", credentials=creds)


# -----------------------
# Send Email Function
# -----------------------
def send_email(to_email: str, attachment_paths: list[str], subject: str, body_text: str):
    """
    Sends an email via Gmail API with local file attachments.

    Parameters:
        to_email: recipient email address
        attachment_paths: list of local file paths to attach
        subject: email subject
        body_text: email body text
    """

    service = get_gmail_service()

    message = MIMEMultipart()
    message["to"] = to_email
    message["subject"] = subject

    # Attach body text
    message.attach(MIMEText(body_text, "plain"))

    # Attach local files
    for file_path in attachment_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        main_type, sub_type = content_type.split("/", 1)

        with open(file_path, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
            encoders.encode_base64(part)

        filename = os.path.basename(file_path)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        message.attach(part)

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent_message = service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

        print(f"Email sent successfully. Message ID: {sent_message['id']}")
        return sent_message

    except HttpError as error:
        print(f"Error sending email: {error}")
        raise
# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    # Example usage
    send_email(
        to_email="recipient@example.com",
        attachment_paths=["Resources/myCV.pdf"],
        subject="Test Job Application",
        body_text="Hello, please see attached files for my application."
    )