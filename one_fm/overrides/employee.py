import frappe
from frappe.utils import getdate, add_days
from frappe.permissions import remove_user_permission
from hrms.overrides.employee_master import *
from one_fm.hiring.utils import (
    employee_after_insert, employee_before_insert, set_employee_name,
    employee_validate_attendance_by_timesheet, set_mandatory_feilds_in_employee_for_Kuwaiti,
)

class EmployeeOverride(EmployeeMaster):
    def validate(self):
        from erpnext.controllers.status_updater import validate_status
        validate_status(self.status, ["Active", "Court Case", "Absconding", "Left","Vacation"])

        self.employee = self.name
        # self.set_employee_name()
        set_employee_name(self, method=None)
        self.validate_date()
        self.validate_email()
        self.validate_status()
        self.validate_reports_to()
        self.validate_preferred_email()
        if self.job_applicant:
            self.validate_onboarding_process()

        if self.user_id:
            self.validate_user_details()
        else:
            existing_user_id = frappe.db.get_value("Employee", self.name, "user_id")
            if existing_user_id:
                remove_user_permission(
                    "Employee", self.name, existing_user_id)
        employee_validate_attendance_by_timesheet(self, method=None)
        

    def before_save(self):
        self.assign_role_profile_based_on_designation()

    def after_insert(self):
        employee_after_insert(self, method=None)
        self.assign_role_profile_based_on_designation()
    
    def before_insert(self):
        employee_before_insert(self, method=None)

    def validate_onboarding_process(self):
        validate_onboarding_process(self)

    def assign_role_profile_based_on_designation(self):
        if self.designation:
            if self.is_new():
                if self.user_id:
                    designation = self.designation
                else:
                    return
            else:
                if self.designation != self.get_doc_before_save().designation:
                    designation = self.designation
                else:
                    return
            role_profile = frappe.db.get_value("Designation", designation, "role_profile")
            if role_profile:
                user = frappe.get_doc("User", self.user_id)
                user.role_profile_name = role_profile
                user.save()
            else:
                frappe.msgprint("Role profile not set in Designation, please set default.")

    def on_update(self):
        super(EmployeeOverride, self).on_update()
        set_mandatory_feilds_in_employee_for_Kuwaiti(self, method=None)
        try:
            current_doc = frappe.get_doc("Employee", self.name)
            if (self.shift != current_doc.shift) and (self.shift_working != current_doc.shift_working):
                frappe.db.sql(f"""
                    DELETE FROM `tabEmployee Schedule` WHERE employee='{self.employee}'
                    AND date>'{getdate()}'
                """)
        except:
            pass

        # clear future employee schedules
        self.clear_schedules()

    def clear_schedules(doc):
        # clear future employee schedules
        todays_date = getdate()
        if doc.status == 'Left' and doc.relieving_date <= todays_date:
            frappe.db.sql(f"""
                DELETE FROM `tabEmployee Schedule` WHERE employee='{doc.name}'
                AND date>'{doc.relieving_date}'
            """)
            frappe.msgprint(f"""
                Employee Schedule cleared for {doc.employee_name} starting from {add_days(doc.relieving_date, 1)} 
            """)