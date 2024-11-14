# Copyright (c) 2024, omar jaber and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today, getdate, month_diff, date_diff

def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
    return [
		_("Employee ID") + ":Data:130",
		_("Employee Name") + ":Data:180",
		_("Employee Status") + ":Data:140",
		_("Designation") + ":Link/Designation:120",
		_("Item Code") + ":Link/Item:180",
		_("Item Name") + ":Data:180",
		_("Issued On") + ":Date:130",
		_("Warehouse") + ":Link/Warehouse:120",
		_("Expire On") + ":Date:120",
		_("Days Left for Expiry") + ":Data:180",
		_("Issued Qty") + ":Data:120",
		_("Returned Qty") + ":Data:120"
	]

def get_data(filters):
	data=[]
	conditions = []

	query = """
		select
			u.employee, u.employee_id, u.employee_name, ui.item, ui.item_name, ui.issued_on, ui.quantity,
			ui.returned, ui.rate, ui.expire_on, u.designation, u.warehouse
		from
			`tabEmployee Uniform` u, `tabEmployee Uniform Item` ui
		where
			u.name = ui.parent and u.type='Issue' and u.docstatus = 1 and ui.quantity > ui.returned
	"""

	if filters.employee:
		query += "and u.employee = '%s' "%filters.employee

	if filters.issued_before:
		query += "and u.issued_on <= '%s' "%filters.issued_before

	uniform_list=frappe.db.sql(query,as_dict=1)
	for uniform in uniform_list:
		employee_status = frappe.db.get_value("Employee", uniform.employee, "status")
		days_left_for_expiry = date_diff(uniform.expire_on, getdate())
		row = [
			uniform.employee_id, uniform.employee_name, employee_status, uniform.designation, uniform.item, uniform.item_name,
			uniform.issued_on, uniform.warehouse, uniform.expire_on, days_left_for_expiry, uniform.quantity, uniform.returned
		]
		data.append(row)

	return data
