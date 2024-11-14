// Copyright (c) 2024, omar jaber and contributors
// For license information, please see license.txt

frappe.query_reports["Uniform Expiry Report"] = {
	"filters": [
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"issued_before",
			"label": __("Issued Before"),
			"fieldtype": "Date",
			"default": frappe.datetime.now_date()
		}
	]
};
