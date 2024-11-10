// Copyright (c) 2024, omar jaber and contributors
// For license information, please see license.txt

frappe.ui.form.on("POC Check", {
	refresh(frm) {
        if(frm.doc.docstatus ==0){
            frm.set_intro("On each row of the MOM POC Table, Update the Action field with the appropriate action for the POC",'blue')
        }
	},
});
