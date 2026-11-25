"""
Comprehensive Smart Campus Management Simulation
------------------------------------------------
A menu-driven program that manages:
1. Student records
2. Attendance
3. Marks
4. Event registration
5. Resource allocation
6. Summary reporting

Uses:
- Conditional statements
- Loops
- Strings
- Lists
- Nested lists
- Tuples
- Tuple unpacking
"""

# ------------------------------
# DATA STRUCTURES
# ------------------------------

# Nested list: [roll_no, name, department, year]
students = []

# Nested list: [roll_no, [attendance for subjects]]
# Example: [101, [1, 0, 1, 1]]
attendance = []

# Nested list: [roll_no, [mark1, mark2, mark3]]
marks = []

# Nested list: [event_id, event_name, [registered_roll_numbers]]
events = []

# List of tuples:
# (resource_id, resource_name, total_quantity, available_quantity)
resources = [
    ("R1", "Projector", 10, 10),
    ("R2", "Laptop", 15, 15),
    ("R3", "Microphone", 20, 20),
    ("R4", "Sports Equipment", 25, 25)
]

# Tuple unpacking example
CAMPUS_NAME, TOTAL_SEMESTERS = ("Smart Campus Management System", 8)


# ------------------------------
# HELPER FUNCTIONS
# ------------------------------

def find_student(roll_no):
    """Return student record if found, otherwise None."""
    for student in students:
        student_roll, name, department, year = student

        if student_roll == roll_no:
            return student

    return None


def find_attendance(roll_no):
    """Return attendance record if found, otherwise None."""
    for record in attendance:
        record_roll, attendance_list = record

        if record_roll == roll_no:
            return record

    return None


def find_marks(roll_no):
    """Return marks record if found, otherwise None."""
    for record in marks:
        record_roll, student_marks = record

        if record_roll == roll_no:
            return record

    return None


def find_event(event_id):
    """Return event record if found, otherwise None."""
    for event in events:
        event_id_value, event_name, registered_students = event

        if event_id_value == event_id:
            return event

    return None


def find_resource(resource_id):
    """Return resource tuple if found, otherwise None."""
    for resource in resources:
        resource_id_value, resource_name, total_qty, available_qty = resource

        if resource_id_value == resource_id:
            return resource

    return None


def get_positive_number(prompt):
    """Get a positive integer from the user."""
    while True:
        try:
            value = int(input(prompt))

            if value > 0:
                return value
            else:
                print("Value must be greater than 0.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def get_mark(prompt):
    """Get a valid mark between 0 and 100."""
    while True:
        try:
            value = int(input(prompt))

            if 0 <= value <= 100:
                return value
            else:
                print("Mark must be between 0 and 100.")

        except ValueError:
            print("Invalid input. Please enter a number.")


# ------------------------------
# STUDENT RECORD MODULE
# ------------------------------

def add_student():
    print("\n----- ADD STUDENT RECORD -----")

    roll_no = input("Enter roll number: ").strip()

    if find_student(roll_no) is not None:
        print("Student with this roll number already exists.")
        return

    name = input("Enter student name: ").strip()
    department = input("Enter department: ").strip()
    year = get_positive_number("Enter year of study: ")

    students.append([roll_no, name, department, year])
    print("Student record added successfully.")


def view_students():
    print("\n----- STUDENT RECORDS -----")

    if len(students) == 0:
        print("No student records available.")
        return

    print(f"{'Roll No':<10}{'Name':<20}{'Department':<15}{'Year':<6}")
    print("-" * 55)

    for student in students:
        roll_no, name, department, year = student
        print(f"{roll_no:<10}{name:<20}{department:<15}{year:<6}")


def search_student():
    print("\n----- SEARCH STUDENT -----")

    roll_no = input("Enter roll number to search: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
    else:
        roll_no, name, department, year = student

        print("\nStudent Found:")
        print(f"Roll Number : {roll_no}")
        print(f"Name        : {name}")
        print(f"Department  : {department}")
        print(f"Year        : {year}")


def update_student():
    print("\n----- UPDATE STUDENT RECORD -----")

    roll_no = input("Enter roll number to update: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
        return

    print("Leave blank and press Enter to keep the existing value.")

    new_name = input(f"Enter new name [{student[1]}]: ").strip()
    new_department = input(f"Enter new department [{student[2]}]: ").strip()

    if new_name != "":
        student[1] = new_name

    if new_department != "":
        student[2] = new_department

    print("Student record updated successfully.")


def delete_student():
    print("\n----- DELETE STUDENT RECORD -----")

    roll_no = input("Enter roll number to delete: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
        return

    students.remove(student)

    attendance_record = find_attendance(roll_no)

    if attendance_record is not None:
        attendance.remove(attendance_record)

    marks_record = find_marks(roll_no)

    if marks_record is not None:
        marks.remove(marks_record)

    print("Student record deleted successfully.")


# ------------------------------
# ATTENDANCE MODULE
# ------------------------------

def mark_attendance():
    print("\n----- MARK ATTENDANCE -----")

    if len(students) == 0:
        print("No students available. Add students first.")
        return

    roll_no = input("Enter roll number: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
        return

    attendance_record = find_attendance(roll_no)

    if attendance_record is None:
        subject_count = get_positive_number("Enter number of subjects: ")
        attendance_list = []

        for i in range(subject_count):
            status = input(f"Enter attendance for subject {i + 1} (P/A): ").strip().upper()

            if status == "P":
                attendance_list.append(1)
            elif status == "A":
                attendance_list.append(0)
            else:
                print("Invalid input. Marked as absent by default.")
                attendance_list.append(0)

        attendance.append([roll_no, attendance_list])
        print("Attendance recorded successfully.")

    else:
        print("Attendance record already exists for this student.")
        print("Existing attendance:", attendance_record[1])


def view_attendance():
    print("\n----- ATTENDANCE RECORDS -----")

    if len(attendance) == 0:
        print("No attendance records available.")
        return

    for record in attendance:
        roll_no, attendance_list = record
        total_subjects = len(attendance_list)
        present_days = sum(attendance_list)

        if total_subjects > 0:
            percentage = (present_days / total_subjects) * 100
        else:
            percentage = 0

        print(f"\nRoll Number: {roll_no}")
        print(f"Attendance : {attendance_list}")
        print(f"Present    : {present_days}/{total_subjects}")
        print(f"Percentage : {percentage:.2f}%")


# ------------------------------
# MARKS MODULE
# ------------------------------

def enter_marks():
    print("\n----- ENTER MARKS -----")

    if len(students) == 0:
        print("No students available. Add students first.")
        return

    roll_no = input("Enter roll number: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
        return

    marks_record = find_marks(roll_no)

    if marks_record is not None:
        print("Marks already entered for this student.")
        return

    subject_count = get_positive_number("Enter number of subjects: ")
    student_marks = []

    for i in range(subject_count):
        mark = get_mark(f"Enter marks for subject {i + 1}: ")
        student_marks.append(mark)

    marks.append([roll_no, student_marks])
    print("Marks entered successfully.")


def view_marks():
    print("\n----- MARKS RECORDS -----")

    if len(marks) == 0:
        print("No marks records available.")
        return

    for record in marks:
        roll_no, student_marks = record
        total = sum(student_marks)
        average = total / len(student_marks)

        if average >= 90:
            grade = "A+"
        elif average >= 80:
            grade = "A"
        elif average >= 70:
            grade = "B"
        elif average >= 60:
            grade = "C"
        elif average >= 50:
            grade = "D"
        else:
            grade = "F"

        print(f"\nRoll Number : {roll_no}")
        print(f"Marks       : {student_marks}")
        print(f"Total       : {total}")
        print(f"Average     : {average:.2f}")
        print(f"Grade       : {grade}")


# ------------------------------
# EVENT REGISTRATION MODULE
# ------------------------------

def create_event():
    print("\n----- CREATE EVENT -----")

    event_id = input("Enter event ID: ").strip()

    if find_event(event_id) is not None:
        print("Event ID already exists.")
        return

    event_name = input("Enter event name: ").strip()
    events.append([event_id, event_name, []])

    print("Event created successfully.")


def register_for_event():
    print("\n----- EVENT REGISTRATION -----")

    if len(events) == 0:
        print("No events available. Create an event first.")
        return

    event_id = input("Enter event ID: ").strip()
    event = find_event(event_id)

    if event is None:
        print("Event not found.")
        return

    roll_no = input("Enter student roll number: ").strip()
    student = find_student(roll_no)

    if student is None:
        print("Student not found.")
        return

    event_id_value, event_name, registered_students = event

    if roll_no in registered_students:
        print("Student is already registered for this event.")
    else:
        registered_students.append(roll_no)
        print(f"{student[1]} registered successfully for {event_name}.")


def view_events():
    print("\n----- EVENT DETAILS -----")

    if len(events) == 0:
        print("No events available.")
        return

    for event in events:
        event_id, event_name, registered_students = event

        print(f"\nEvent ID    : {event_id}")
        print(f"Event Name  : {event_name}")
        print(f"Registered  : {len(registered_students)} student(s)")

        if len(registered_students) > 0:
            print("Roll Numbers:", ", ".join(registered_students))
        else:
            print("No students registered yet.")


# ------------------------------
# RESOURCE ALLOCATION MODULE
# ------------------------------

def view_resources():
    print("\n----- AVAILABLE RESOURCES -----")

    print(f"{'ID':<6}{'Resource':<22}{'Total':<8}{'Available':<10}")
    print("-" * 50)

    for resource in resources:
        resource_id, resource_name, total_qty, available_qty = resource
        print(f"{resource_id:<6}{resource_name:<22}{total_qty:<8}{available_qty:<10}")


def allocate_resource():
    print("\n----- ALLOCATE RESOURCE -----")

    resource_id = input("Enter resource ID: ").strip()
    resource = find_resource(resource_id)

    if resource is None:
        print("Resource not found.")
        return

    resource_id, resource_name, total_qty, available_qty = resource

    if available_qty == 0:
        print(f"No {resource_name} available.")
        return

    quantity = get_positive_number("Enter quantity to allocate: ")

    if quantity > available_qty:
        print(f"Only {available_qty} {resource_name}(s) available.")
    else:
        available_qty -= quantity

        updated_resource = (resource_id, resource_name, total_qty, available_qty)
        index = resources.index(resource)
        resources[index] = updated_resource

        print(f"{quantity} {resource_name}(s) allocated successfully.")
        print(f"Remaining {resource_name}: {available_qty}")


def return_resource():
    print("\n----- RETURN RESOURCE -----")

    resource_id = input("Enter resource ID: ").strip()
    resource = find_resource(resource_id)

    if resource is None:
        print("Resource not found.")
        return

    resource_id, resource_name, total_qty, available_qty = resource
    quantity = get_positive_number("Enter quantity to return: ")

    if available_qty + quantity > total_qty:
        print("Invalid return quantity. It exceeds the total resource quantity.")
    else:
        available_qty += quantity

        updated_resource = (resource_id, resource_name, total_qty, available_qty)
        index = resources.index(resource)
        resources[index] = updated_resource

        print(f"{quantity} {resource_name}(s) returned successfully.")
        print(f"Available {resource_name}: {available_qty}")


# ------------------------------
# SUMMARY REPORT MODULE
# ------------------------------

def summary_report():
    print("\n===== SMART CAMPUS SUMMARY REPORT =====")
    print(f"Campus System: {CAMPUS_NAME}")
    print(f"Total Semesters: {TOTAL_SEMESTERS}")

    print(f"\nTotal Students          : {len(students)}")
    print(f"Total Attendance Records: {len(attendance)}")
    print(f"Total Marks Records     : {len(marks)}")
    print(f"Total Events            : {len(events)}")

    total_registered = 0

    for event in events:
        event_id, event_name, registered_students = event
        total_registered += len(registered_students)

    print(f"Total Event Registrations: {total_registered}")

    print("\nResource Availability:")

    for resource in resources:
        resource_id, resource_name, total_qty, available_qty = resource
        print(f"{resource_name:<22}: {available_qty}/{total_qty} available")

    if len(marks) > 0:
        total_marks = 0
        total_subjects = 0

        for record in marks:
            roll_no, student_marks = record
            total_marks += sum(student_marks)
            total_subjects += len(student_marks)

        campus_average = total_marks / total_subjects
        print(f"\nCampus Average Marks: {campus_average:.2f}")

    else:
        print("\nNo marks data available for campus average.")


# ------------------------------
# MAIN MENU
# ------------------------------

def main_menu():
    while True:
        print("\n======================================")
        print("   SMART CAMPUS MANAGEMENT SYSTEM")
        print("======================================")
        print("1. Student Records")
        print("2. Attendance Management")
        print("3. Marks Management")
        print("4. Event Registration")
        print("5. Resource Allocation")
        print("6. Summary Report")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            while True:
                print("\n----- STUDENT RECORD MENU -----")
                print("1. Add Student")
                print("2. View Students")
                print("3. Search Student")
                print("4. Update Student")
                print("5. Delete Student")
                print("6. Back to Main Menu")

                student_choice = input("Enter your choice (1-6): ").strip()

                if student_choice == "1":
                    add_student()
                elif student_choice == "2":
                    view_students()
                elif student_choice == "3":
                    search_student()
                elif student_choice == "4":
                    update_student()
                elif student_choice == "5":
                    delete_student()
                elif student_choice == "6":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "2":
            while True:
                print("\n----- ATTENDANCE MENU -----")
                print("1. Mark Attendance")
                print("2. View Attendance")
                print("3. Back to Main Menu")

                attendance_choice = input("Enter your choice (1-3): ").strip()

                if attendance_choice == "1":
                    mark_attendance()
                elif attendance_choice == "2":
                    view_attendance()
                elif attendance_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "3":
            while True:
                print("\n----- MARKS MENU -----")
                print("1. Enter Marks")
                print("2. View Marks")
                print("3. Back to Main Menu")

                marks_choice = input("Enter your choice (1-3): ").strip()

                if marks_choice == "1":
                    enter_marks()
                elif marks_choice == "2":
                    view_marks()
                elif marks_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "4":
            while True:
                print("\n----- EVENT REGISTRATION MENU -----")
                print("1. Create Event")
                print("2. Register Student for Event")
                print("3. View Events")
                print("4. Back to Main Menu")

                event_choice = input("Enter your choice (1-4): ").strip()

                if event_choice == "1":
                    create_event()
                elif event_choice == "2":
                    register_for_event()
                elif event_choice == "3":
                    view_events()
                elif event_choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "5":
            while True:
                print("\n----- RESOURCE ALLOCATION MENU -----")
                print("1. View Resources")
                print("2. Allocate Resource")
                print("3. Return Resource")
                print("4. Back to Main Menu")

                resource_choice = input("Enter your choice (1-4): ").strip()

                if resource_choice == "1":
                    view_resources()
                elif resource_choice == "2":
                    allocate_resource()
                elif resource_choice == "3":
                    return_resource()
                elif resource_choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "6":
            summary_report()

        elif choice == "7":
            print("\nExiting Smart Campus Management System...")
            print("Thank you for using the system!")
            break

        else:
            print("Invalid choice. Please enter a number from 1 to 7.")


# ------------------------------
# PROGRAM START
# ------------------------------

if __name__ == "__main__":
    main_menu()

    