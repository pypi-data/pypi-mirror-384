#scheduler.py
import schedule
import time

def schedule_reminders(students_manager, reminder_generator, reminder_sender, logger):
    """Schedule reminder delivery for each student at their preferred time."""
    print("##### Started The Student Reminder App #####")
    
    for student in students_manager.get_students():
        reminder = reminder_generator(student['name'], student['course'])
        schedule.every().day.at(student['preferred_time']).do(lambda s=student, r=reminder: (reminder_sender(s['email'], r), logger.log_reminder(s, r)))

    while True:
        schedule.run_pending()
        logger.log_scheduler_started()
        time.sleep(30) # Check every minute        
