# logger.py
import datetime

def log_reminder(student, reminder):
    """Log a sent reminder with a timestamp to a file."""
    with open("reminder_log.txt","a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Sent to {student['name']}:{reminder}\n")


def log_scheduler_started():
    print(datetime.datetime.now(), "- Checking for new events...")
    with open("reminder_log.txt","a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Checking for new events...\n")
