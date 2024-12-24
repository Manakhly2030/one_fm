# Copyright (c) 2024, omar jaber and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from frappe.utils import getdate, get_last_day
from one_fm.operations.doctype.operations_shift.operations_shift import get_shift_supervisor

class DefaultShiftChecker(Document):
    pass


def create_default_shift_checker():
    start_date = getdate()
    last_day_of_month = get_last_day(start_date)
    
    threshold =  frappe.db.get_single_value("ONEFM General Setting", "default_shift_checker_threshold")

    Employee = DocType("Employee")
    EmployeeSchedule = DocType("Employee Schedule")

    query = (
        frappe.qb.from_(Employee)
        .join(EmployeeSchedule)
        .on(Employee.name == EmployeeSchedule.employee)
        .select(
            Employee.name,
            Employee.employee_name,
            EmployeeSchedule.shift.as_("scheduled_shift"),
            Employee.shift.as_("default_shift"),
            EmployeeSchedule.site,
            Count(EmployeeSchedule.shift).as_("operations_shift_count"),
        )
        .where(
            (Employee.shift_working == 1)
            & (Employee.shift.isnotnull())
            & (Employee.shift != EmployeeSchedule.shift)
            & (EmployeeSchedule.employee_availability == "Working")
            & (EmployeeSchedule.roster_type == "Basic")
            & (EmployeeSchedule.date[start_date:last_day_of_month])
        )
        .groupby(Employee.name, EmployeeSchedule.shift)
        .having(Count(EmployeeSchedule.shift) > threshold)
    )

    result = query.run(as_dict=1)

    grouped_data = defaultdict(list)
    for item in result:
        grouped_data[(item["scheduled_shift"], item["site"])].append(item)

    for key, employees in grouped_data.items():
        shift, site = key
        try:
            default_shift_checker = frappe.new_doc("Default Shift Checker")
            default_shift_checker.start_date = start_date
            default_shift_checker.end_date = last_day_of_month
            default_shift_checker.operations_shift = shift

            site_supervisor = frappe.db.get_value("Operations Site", site, "account_supervisor")
            shift_supervisor = get_shift_supervisor(shift)
            default_shift_checker.site_supervisor = site_supervisor
            default_shift_checker.shift_supervisor = shift_supervisor

            for employee in employees:
                default_shift_checker.append("employees_assigned_outside_default_shift", {
                    "employee": employee.name,
                    "employee_name": employee.employee_name,
                    "count": employee.operations_shift_count
                })
            default_shift_checker.save()
        except Exception as e:
            frappe.log_error("Default Shift Checker", frappe.get_traceback())
            continue
