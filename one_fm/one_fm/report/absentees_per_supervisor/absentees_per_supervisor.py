# Copyright (c) 2013, omar jaber and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days
from datetime import datetime
import datetime
# import operator
import re
from datetime import date
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Operations Shift") + ":Link/Operations Shift:250",
		_("Shift Supervisor Name") + ":Link/Operations Shift:250",
		_("Operations Site") + ":Link/Operations Site:300",
		_("Site Supervisor Name") + ":Data:250",
		_("Number of Absentees") + ":Int:150",
	]

def get_data(filters=None):
	if not filters.get("start_date") or not filters.get("end_date"):
		frappe.throw(_("Please specify Start Date and End Date"))

	grouped_data = get_absent_employees(filters.start_date,filters.end_date,filters.roster_type)

	final_data = []
	for shift, count in grouped_data:
		if shift:
			shift_doc = frappe.get_doc("Operations Shift", shift)
			first_shift_supervisor = None
			if shift_doc.shift_supervisor:
				first_shift_supervisor = shift_doc.shift_supervisor[0].supervisor_name

			site_name = shift_doc.site
			site_doc = frappe.get_doc("Operations Site", site_name) if site_name and frappe.db.exists("Operations Site", site_name) else None
			final_data.append([
				shift_doc.name,  # Operations Shift Name
				first_shift_supervisor or "N/A",  # Shift Supervisor Name
				site_name or "N/A",  # Operations Site Name
				site_doc.account_supervisor_name if site_doc else "N/A",  # Site Supervisor Name
				count,  # Number of Absentees
			])
	return final_data



def get_absent_employees(start_date, end_date,roster_type):
	attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "attendance_date": ["between", [start_date, end_date]],
            "status": "Absent",
			"roster_type":roster_type,
        },
         fields=["employee", "operations_shift", "attendance_date"])
	grouped_data = {}
	for record in attendance_records:
		shift = record.get("operations_shift")
		if shift not in grouped_data:
			grouped_data[shift] = 0
		grouped_data[shift] += 1
	sorted_shifts = sorted(grouped_data.items(), key=lambda x: x[1], reverse=True)

	return sorted_shifts

