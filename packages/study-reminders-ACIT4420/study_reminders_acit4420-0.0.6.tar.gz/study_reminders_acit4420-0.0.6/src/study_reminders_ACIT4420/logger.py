# logger.py
import datetime

def log_added_student(name):

    with open("reminder_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Added student {name}\n")

def log_removed_student(name):

    with open("reminder_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Removed student {name}\n")

def log_generated_reminder(email, reminder):
    """Log generated reminder with a timestamp to a file."""
    with open("reminder_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Generated {email}:{reminder}\n")

def log_scheduler():
    """Log start of scheduler with a timestamp to a file."""
    with open("reminder_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Daily Scheduler Started\n")

def log_sent_reminder(name, reminder):
    """Log sent reminder with a timestamp to a file."""
    with open("reminder_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Sent to {name}:{reminder}\n")

