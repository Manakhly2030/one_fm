# Copyright (c) 2024, omar jaber and contributors
# For license information, please see license.txt

import frappe
from frappe.desk.form.assign_to import remove
from erpnext.crm.utils import get_open_todos
from frappe.model.document import Document


class POCCheck(Document):
	def on_submit(self):
		for each in self.mom_poc_table:
			if each.action not in ['Do Nothing',"Update POC"]:
				frappe.throw(f"Please set an action for row {each.idx} in MOM POC Table")
		self.remove_assignments()
		self.update_poc_details()
	
	def remove_assignments(self):
		open_todo = get_open_todos("POC Check",self.name)
		if open_todo:
			for each in open_todo:
				remove("POC Check",self.name,each.allocated_to,ignore_permissions=1)
	
	def update_poc_details(self):
		for each in self.mom_poc_table:
			if each.action == "Update POC":
				destination_dict = {"Operations Site":["Operations Site"],'Project':['Project'],'Both':["Operations Site","Project"]}
				if destination_dict.get(each.destination):
					for one in destination_dict.get(each.destination):
						try:
							existing_row = frappe.get_doc("POC",{'parenttype':one,'parent':self.project if one == "Project" else self.site,'poc':each.poc_name})
							if existing_row:
								existing_row.poc = each.new_poc_name
								existing_row.designation = each.new_poc_designation
								existing_row.save()
						except frappe.DoesNotExistError:
							frappe.throw(f"Please note that <b>{each.poc_name}</b> is not set as a POC in <b>{one}</b> <b>{self.project if one=='Project' else self.site}</b>")
					
     

