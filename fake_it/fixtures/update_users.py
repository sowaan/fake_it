import frappe
from tqdm import tqdm

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
        # print(user_id, prefered_email)
        user = frappe.get_doc("User", user_id)
        # print(user.name)
        # Update the name field directly
        user.name = prefered_email  # Set the user email as the name (No need for renaming)

        frappe.db.set_value("User", user_id, "first_name", first_name, update_modified=False)
        frappe.db.set_value("User", user_id, "middle_name", middle_name, update_modified=False)
        frappe.db.set_value("User", user_id, "last_name", last_name, update_modified=False)
        frappe.db.set_value("User", user_id, "full_name", f"{first_name} {middle_name} {last_name}", update_modified=False)
        frappe.db.set_value("User", user_id, "email", prefered_email, update_modified=False)
        frappe.db.set_value("User", user_id, "username", prefered_email, update_modified=False)
        frappe.db.set_value("User", user_id, "name", prefered_email, update_modified=False)

        # user.first_name = first_name
        # user.middle_name = middle_name
        # user.last_name = last_name
        # user.full_name = f"{first_name} {middle_name} {last_name}"

        # # Save the changes to the user record
        # user.save(ignore_permissions=True)

        # Update linked records for this user
        update_linked_user_fields(user_id, prefered_email)
    except frappe.DoesNotExistError:
        print(f"User {user_id} does not exist. Skipping.")
    except Exception as e:
        print(f"Failed to update User {user_id}: {str(e)}")

def update_linked_user_fields(user_id, new_user_id):
    """
    Updates linked fields referencing the User in other doctypes.

    :param user_id: The current User ID (email).
    :param new_user_id: The new User ID (email) to update in linked records.
    """
    # print(update_linked_user_fields)
    # print(user_id, new_user_id)
    try:
        # Find all DocTypes where the User is linked by user_id (or any custom field)
        linked_fields = frappe.get_all(
            "DocField",
            filters={"fieldtype": "Link", "options": "User"},
            fields=["parent", "fieldname"]
        )

        for field in linked_fields:
            # Find all documents linked to the old User ID
            if not is_single_doctype(field["parent"]):
                linked_docs = frappe.get_all(
                    field["parent"],
                    filters={field["fieldname"]: user_id},
                    fields=["name"]
                )

                for doc in linked_docs:
                    # Update the user_id (or any field that references User)
                    frappe.db.set_value(
                        field["parent"],
                        doc["name"],
                        field["fieldname"],  # The field that references User
                        new_user_id,
                        update_modified=False
                    )

        # print(f"Updated linked records for User {user_id}.")

    except Exception as e:
        print(f"Failed to update linked records for User {user_id}: {str(e)}")


def is_single_doctype(doctype_name):
    """
    Check if the given doctype is a single doctype.

    :param doctype_name: The name of the doctype to check.
    :return: True if it's a single doctype, False otherwise.
    """
    doc_type = frappe.get_doc("DocType", doctype_name)
    return doc_type.issingle


def update_users():
    """
    Updates User records for employees who have been anonymized.
    """
    employees = frappe.get_all(
        "Employee",
        filters={"user_id": ["is", "set"]},
        fields=["name", "user_id", "first_name", "middle_name", "last_name", "prefered_email"]
    )

    for emp in tqdm(employees, desc="Processing Users", unit="user"):
        if emp.get("user_id") and emp.get("prefered_email"):
            update_user(
                user_id=emp["user_id"],
                prefered_email=emp["prefered_email"],
                first_name=emp["first_name"],
                middle_name=emp["middle_name"],
                last_name=emp["last_name"]
            )

    frappe.db.commit()
    print("User data update completed!")
