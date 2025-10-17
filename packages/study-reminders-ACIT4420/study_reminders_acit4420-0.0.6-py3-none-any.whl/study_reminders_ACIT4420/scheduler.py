# scheduler.py
import schedule
import time

from .  import logger
from . import reminder_sender
from . import reminder_generator

def schedule_reminders(students_manager_object):
    """Schedule reminder delivery for each student at their preferred time."""
    for student in students_manager_object.get_students():
        reminder = reminder_generator.generate_reminder(student['name'], student['course'])
        schedule.every().day.at(student['preferred_time']).do(
            lambda s=student, r=reminder: (reminder_sender.send_reminder(s['email'], r)))
    logger.log_scheduler()
    print("Scheduler Started")
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute