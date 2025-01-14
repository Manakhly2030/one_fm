frappe.ui.form.on('Contact', {
    after_save: function (frm) {

        // Construct the new name based on the form data
        let new_name = (frm.doc.first_name + " " + frm.doc.last_name).trim();
        console.log("Constructed New Name:", new_name);

        // Check if the new name is different from the current doc name
        if (new_name !== frm.doc.name) {
            console.log("Name has changed. Redirecting to the updated URL...");
            let new_url = frappe.urllib.get_base_url() + '/app/contact/' + encodeURIComponent(new_name);
            window.location.href = new_url;
        }
    }
});
