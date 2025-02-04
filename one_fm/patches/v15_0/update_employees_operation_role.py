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
    employee_names = []
    for schedule in results:
        if schedule["schedule_shift"] and schedule["current_shift"] == schedule["schedule_shift"]:
            updates.append((schedule["operations_role"], schedule["employee"]))
            employee_names.append(schedule["employee"])

    # Execute bulk update if there are matching records
    if updates:
        update_cases = []
        employee_ids = []
        for operations_role, employee_name in updates:
            update_cases.append("WHEN %s THEN %s")
            employee_ids.append(employee_name)  # Add employee name
            employee_ids.append(operations_role)  # Add corresponding operation role

        # Add the WHERE clause parameters
        employee_ids.extend(employee_names)

        # Bulk update query
        update_query = f"""
            UPDATE `tabEmployee`
            SET custom_operations_role_allocation = CASE name
                {' '.join(update_cases)}
            END
            WHERE name IN ({', '.join(['%s'] * len(employee_names))})
        """
        # Execute the query
        frappe.db.sql(update_query, tuple(employee_ids))
        frappe.db.commit()