// Copyright (c) 2025, omar jaber and contributors
// For license information, please see license.txt

frappe.query_reports["Absentees Per Supervisor"] = {
	"filters": [
		{
            "fieldname": "start_date",
            "label": __("Start Date"),
            "fieldtype": "Date",
			'default':new Date(new Date().getFullYear(), new Date().getMonth(), 1),
            "reqd": 1,
        },
        {
			"fieldname": "end_date",
            "label": __("End Date"),
			"fieldtype": "Date",
			'default':frappe.datetime.add_days(frappe.datetime.get_today(), -1),
            "reqd": 1,
        },
		{
			"fieldname":"roster_type",
			"label": __("Roster Type"),
			"fieldtype": "Select",
			"options": "\nBasic\nOver-Time",
			"reqd": 0
		},
	]
};
