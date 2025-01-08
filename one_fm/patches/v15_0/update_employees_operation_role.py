import frappe

@frappe.whitelist()
def execute():
    # Fetch all employees and their schedules in a single query
    query = """
        SELECT e.name AS employee, e.shift AS current_shift, es.shift AS schedule_shift, es.operations_role
        FROM `tabEmployee` AS e
        LEFT JOIN (
            SELECT es.employee, es.shift, es.operations_role
            FROM `tabEmployee Schedule` AS es
            WHERE es.roster_type = 'Basic'
            AND es.employee_availability = 'Working'
            AND es.date = (
                SELECT MAX(date)
                FROM `tabEmployee Schedule` AS sub
                WHERE sub.employee = es.employee
            )
        ) AS es
        ON e.name = es.employee
        WHERE e.shift_working = 1 AND e.status = 'Active';
    """
    results = frappe.db.sql(query, as_dict=True)

    # Prepare bulk update data
    updates = []
    for schedule in results:
        if schedule["schedule_shift"] and schedule["current_shift"] == schedule["schedule_shift"]:
            updates.append((schedule["operations_role"], schedule["employee"]))

    # Execute bulk update if there are matching records
    if updates:
        update_query = """
            UPDATE `tabEmployee`
            SET custom_operations_role_allocation = CASE name
        """
        update_cases = []
        employee_ids = []
        for operations_role, employee_name in updates:
            update_cases.append(f"WHEN '{employee_name}' THEN '{operations_role}'")
            employee_ids.append(f"'{employee_name}'")
        
        # Combine the query
        update_query += " ".join(update_cases) + " END WHERE name IN (" + ", ".join(employee_ids) + ")"

        # Execute the query
        frappe.db.sql(update_query)
        frappe.db.commit()
    return results
