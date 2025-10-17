# reminder_generator.py
from . import logger

# barely changed from provided code, only added the logger

def generate_reminder(name, course):
    """Generate a personalized study reminder for the given name and course."""
    logger.log_generated_reminder(name, course)
    return f"Hi {name}, remember to review {course} materials before the deadline!"