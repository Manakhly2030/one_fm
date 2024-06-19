import requests, frappe

@frappe.whitelist()
def log_pivotal_tracker(**kwargs):
    """
        Log Pivotal Tracker story from HD Ticket doc
    """
    try:
        doc = frappe.get_doc("HD Ticket", frappe.form_dict.name)
        description = frappe.form_dict.description
        doc_link = frappe.utils.get_url(doc.get_url())
        default_api_integration = frappe.get_doc("Default API Integration")

        pivotal_tracker = frappe.get_doc("API Integration",
            [i for i in default_api_integration.integration_setting
                if i.app_name=='Pivotal Tracker'][0].app_name)
        if pivotal_tracker.active:
            headers={"X-TrackerToken":pivotal_tracker.get_password('api_token').replace(' ', ''),
                "Content-Type": "application/json"}
            project_id = pivotal_tracker.get_password('project_id').replace(' ', '')
            url = f"{pivotal_tracker.url}/services/v5/projects/{project_id}/stories"

            req = requests.post(
                url=url,
                headers=headers,
                json={"name":doc.subject,
                'description':f"""Link:\t{doc_link}\nStatus: \t{doc.status}\nPriority: \t{doc.priority}\Ticket Type: \t{doc.ticket_type}\n\n
                {description}""",
                'story_type':'bug',},
                timeout=5
            )
            if(req.status_code==200):
                response_data = frappe._dict(req.json())
                doc.db_set('pivotal_tracker', f"{pivotal_tracker.url}/n/projects/{project_id}/stories/{response_data.id}")
                return {'status':'success'}
            else:
                frappe.throw(f"Pivotal Tracker story could not be created:\n {req.json()}")
    except Exception as e:
        frappe.throw(f"Pivotal Tracker story could not be created:\n {str(e)}")
        frappe.log_error(str(e), 'HD Ticket Pivotal Tracker')
