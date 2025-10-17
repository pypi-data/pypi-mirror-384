# reminder_sender.py

from . import logger

# barely changed from the provided code, only adding the logger

def send_reminder(email, reminder):
    """Simulate sending a reminder to the specified email."""
    if not email:
        raise ValueError("Email address is missing")
    print(f"Sending reminder to {email}: {reminder}")
    logger.log_sent_reminder(email, reminder)
    