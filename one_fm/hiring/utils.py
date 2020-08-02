# -*- coding: utf-8 -*-
# encoding: utf-8
from __future__ import unicode_literals
import frappe
from frappe.utils import get_url

def after_insert_job_applicant(doc, method):
    website_user_for_job_applicant(doc.email_id, doc.one_fm_first_name, doc.one_fm_last_name, doc.one_fm_applicant_password)
    notify_recruiter_and_requester_from_job_applicant(doc, method)

def website_user_for_job_applicant(email_id, first_name, last_name='', applicant_password=False):
    if not frappe.db.exists ("User", email_id):
        from frappe.utils import random_string
        user = frappe.get_doc({
            "doctype": "User",
            "first_name": first_name,
            "last_name": last_name,
            "email": email_id,
            "user_type": "Website User",
            "send_welcome_email": False
        })
        user.flags.ignore_permissions=True
        # user.reset_password_key=random_string(32)
        user.add_roles("Job Applicant")
        if applicant_password:
            from frappe.utils.password import update_password
            update_password(user=user.name, pwd=applicant_password)
        return user

def notify_recruiter_and_requester_from_job_applicant(doc, method):
    if doc.one_fm_erf:
        recipients = []
        erf_details = frappe.db.get_values('ERF', filters={'name': doc.one_fm_erf},
        fieldname=["erf_requested_by", "recruiter_assigned", "secondary_recruiter_assigned"], as_dict=True)
        if erf_details and len(erf_details) == 1:
            if erf_details[0].erf_requested_by and erf_details[0].erf_requested_by != 'Administrator':
                recipients.append(erf_details[0].erf_requested_by)
            if erf_details[0].recruiter_assigned:
                recipients.append(erf_details[0].recruiter_assigned)
            if erf_details[0].secondary_recruiter_assigned:
                recipients.append(erf_details[0].secondary_recruiter_assigned)
        designation = frappe.db.get_value('Job Opening', doc.job_title, 'designation')
        page_link = get_url("/desk#Form/Job Applicant/" + doc.name)
        message = "<p>There is a Job Application created for the position {2} <a href='{0}'>{1}</a></p>".format(page_link, doc.name, designation)

        if recipients:
            frappe.sendmail(
                recipients= recipients,
                subject='Job Application created for {0}'.format(designation),
                message=message,
                reference_doctype=doc.doctype,
                reference_name=doc.name
            )
