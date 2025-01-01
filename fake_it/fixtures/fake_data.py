import frappe
from faker import Faker
from tqdm import tqdm

def anonymize_employee_data(fields_to_anonymize):
    """
    Anonymizes specified fields in the Employee doctype and updates linked records.

    :param fields_to_anonymize: A dictionary where keys are field names and values are Faker methods.
                                Example: {"first_name": "first_name", "email": "email"}
    """
    fake = Faker()

    # Fetch all employees
    employees = frappe.get_all(
        "Employee",
        fields=["name", "prefered_contact_email", "personal_email", "company_email", 'prefered_email', "user_id"] + list(fields_to_anonymize.keys()),
        # filters={"name": "KHI-01269"}
    )

    print("Anonymizing employee data...")
    for emp in tqdm(employees, desc="Processing Employees", unit="employee"):
        updates = {}

        # Update fields based on Faker
        for field, faker_method in fields_to_anonymize.items():
            if hasattr(fake, faker_method):
                updates[field] = getattr(fake, faker_method)()

        # Handle gender-specific name generation
        if emp.get("gender") == "Female":
            updates["first_name"] = fake.first_name_female()
            updates["middle_name"] = fake.first_name_female()
            updates["last_name"] = fake.last_name()
        elif emp.get("gender") == "Male":
            updates["first_name"] = fake.first_name_male()
            updates["middle_name"] = fake.first_name_male()
            updates["last_name"] = fake.last_name()
        else:
            updates["first_name"] = fake.first_name()
            updates["middle_name"] = fake.first_name()
            updates["last_name"] = fake.last_name()

        # Ensure employee_name is first_name + middle_name + last_name
        updates["employee_name"] = f"{updates['first_name']} {updates['middle_name']} {updates['last_name']}"


        # Handle prefered_email logic
        if emp.get("prefered_contact_email") == "Company Email" and updates.get("company_email"):
            updates["prefered_email"] = updates["company_email"]
        elif emp.get("prefered_contact_email") == "Personal Email" and updates.get("personal_email"):
            updates["prefered_email"] = updates["personal_email"]


        # Update User associated with the Employee
        if emp.get("user_id") and updates.get("prefered_email"):
            update_user(
                user_id=emp["user_id"],
                prefered_email=updates["prefered_email"],
                first_name=updates["first_name"],
                middle_name=updates["middle_name"],
                last_name=updates["last_name"],
            )
            updates["user_id"] = updates["prefered_email"]  # Update Employee's user_id to match the new User email

        # Update Employee record
        for field, value in updates.items():
            frappe.db.set_value(
                "Employee",
                emp.name,
                field,
                value,
                update_modified=False  # Prevents updating `updated_on` and `updated_by`
            )

        # Update linked records for employee_name
        if "employee_name" in updates:
            update_employee_name_links(emp.name, updates["employee_name"])
            update_timesheet_titles(emp.name, updates["employee_name"])

    frappe.db.commit()
    print("Employee data anonymization completed!")

def update_employee_name_links(employee_id, new_employee_name):
    """
    Updates the fetched employee_name field in linked doctypes.

    :param employee_id: The Employee ID whose name is being updated.
    :param new_employee_name: The new name for the employee.
    """
    # Find doctypes where employee_name is fetched from Employee
    linked_fields = frappe.get_all(
        "DocField",
        filters={"fieldname": "employee_name", "fetch_from": "employee.employee_name"},
        fields=["parent", "fieldname"]
    )

    for field in linked_fields:
        # Find all documents with the linked Employee ID
        linked_docs = frappe.get_all(
            field["parent"],
            filters={"employee": employee_id},
            fields=["name"]
        )

        # Update the fetched employee_name field in each linked document
        for doc in linked_docs:
            frappe.db.set_value(field["parent"], doc["name"], "employee_name", new_employee_name, update_modified=False)

    # print(f"Updated employee_name links for Employee ID {employee_id}")

def update_timesheet_titles(employee_id, new_employee_name):
    """
    Updates the title field in Timesheet records linked to the Employee.

    :param employee_id: The Employee ID whose name is being updated.
    :param new_employee_name: The new name for the employee.
    """
    # Fetch Timesheet records linked to the Employee
    timesheet_records = frappe.get_all(
        "Timesheet",
        filters={"employee": employee_id},
        fields=["name", "title"]
    )

    for record in timesheet_records:
        # Update the title with the new employee name
        new_title = new_employee_name
        frappe.db.set_value("Timesheet", record["name"], "title", new_title, update_modified=False)

    # print(f"Updated Timesheet titles for Employee ID {employee_id}")

def update_user(user_id, prefered_email, first_name, middle_name, last_name):
    """
    Update the User associated with the Employee.

    :param user_id: Current User ID (email).
    :param prefered_email: New email to set for the User.
    :param first_name: New first name.
    :param middle_name: New middle name.
    :param last_name: New last name.
    """
    try:
        # Fetch the User
        user = frappe.get_doc("User", user_id)

        # Update the User details
        # user.name = prefered_email
        # user.email = prefered_email
        user.first_name = first_name
        user.middle_name = middle_name
        user.last_name = last_name
        user.full_name = f"{first_name} {middle_name} {last_name}"

        # Save changes to the User
        user.save(ignore_permissions=True)
        # print(prefered_email)
        # Rename the User to match the new email
        frappe.rename_doc("User", user_id, prefered_email)

        # print(f"Updated and renamed User: {user_id} -> {prefered_email}")
    except frappe.DoesNotExistError:
        print(f"User {user_id} does not exist. Skipping.")
    except Exception as e:
        print(f"Failed to update User {user_id}: {str(e)}")

# Execute the script
def anonymize_data():
    """
    Specify the fields to anonymize and the corresponding Faker methods.
    """
    fields_to_anonymize = {
        "first_name": "first_name",
        "last_name": "last_name",
        "cell_number": "phone_number",
        "personal_email": "email",
        "company_email":"company_email",
        "permanent_address": "address",
        "person_to_be_contacted":"name",
        "emergency_phone_number": "phone_number",
        "nic_numbar":"msisdn",
        "passport_number":"passport_number"
    }
    anonymize_employee_data(fields_to_anonymize)
    print("Anonymization process completed successfully!")



