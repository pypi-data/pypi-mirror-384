# students.py
class Students:
    """Class to manage a list of students' information."""

    def __init__(self):
        self.students = []

    def add_student(self, name, contact_info, course, preferred_time="08:00 AM"):
        """Add a student with name, contact info, course, and preferred reminder time. """
        student = { 'name': name, 'contact_info': contact_info, 'course': course, 'preferred_time': preferred_time }
        self.students.append(student)
    
    def remove_student(self, name):
        """Remove a student by name."""
        self.students = [s for s in self.students if s['name'] != name]

    def get_students(self):
        """Retrieve the list of students."""
        return self.students