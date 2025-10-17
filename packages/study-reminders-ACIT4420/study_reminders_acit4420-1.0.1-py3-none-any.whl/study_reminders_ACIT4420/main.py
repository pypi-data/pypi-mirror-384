# from . is needed in order to ensure python checks the files within same folder in order to use the desired modules
from . import logger
from . import reminder_sender
from . import reminder_generator
from . import scheduler
from . import students_manager


# this main file is fairly simple, starts with an object initializer of the student_manager class

students_manager_object = students_manager.StudentsManager()

# then an infinite loop which functions as the main way for input and output for the user

# the code itself should be decently intuitive to understand

while True:
    print("\nstudy_reminders module begun")
    print("Enter the number of the option to continue")
    print("1. Start Daily Scheduler")
    print("2. Add Student")
    print("3. Remove Student")
    print("4. List Students")
    print("5. Simulate Schedule Sending")
    print("6. Quit")
    answer = input()

    if answer == "1":
        scheduler.schedule_reminders(students_manager_object)
    elif answer == "2":
        print("Enter name of the student")
        name = input()
        print("Enter email of the student")
        email = input()
        print("Enter course of the student")
        course = input()
        print("Enter preferred reminder time of the student, in HH:MM format")
        preferred_time = input()
        students_manager_object.add_student(name, email, course, preferred_time)
        print(f"Student {name} added successfully")
        logger.log_added_student(name)
    elif answer == "3":
        print("Enter name of the student to be removed")
        name = input()
        students_manager_object.remove_student(name)
        print(f"Student {name} removed successfully")
        logger.log_removed_student(name)
    elif answer == "4":
        students_manager_object.list_students()
    elif answer == "5":
        students = students_manager_object.get_students()
        for i in students:
            name = i['name']
            course = i['course']
            reminder = reminder_generator.generate_reminder(name, course)
            email = i['email']
            reminder_sender.send_reminder(email, reminder)
    elif answer == "6":
        exit(0)