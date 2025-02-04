frappe.ui.form.on('Issue', {
    refresh:function(frm){
      // set pivotal tracker button
      pivotal_tracker_button(frm);
      add_pivotal_section(frm);
      set_issue_type_filter(frm);
      set_whatsapp_reply_button(frm);
    },
    department: function(frm) {
      set_issue_type_filter(frm);
    }
});

var set_issue_type_filter = frm => {
  var filters = {};
  if(frm.doc.department){
    filters['department'] = frm.doc.department;
  }
  frm.set_query("issue_type", function() {
    return {
      query: "one_fm.utils.get_issue_type_in_department",
      filters: filters
    }
  });
};


let pivotal_tracker_button = frm => {
  // add a link in dashboard section if issue has been added to pivotal tracker
  if(['Open', 'Replied', 'On Hold'].includes(frm.doc.status) && (frappe.user.has_role('System Manager') || frappe.user.has_role('Issue User')) && !frm.doc.pivotal_tracker){
    frm.add_custom_button('Pivotal Tracker', () => {
      frappe.confirm('Are you sure you create Pivotal Tracker story?',
        () => {
            let description = ``;
            if (!frm.doc.description){
              description = frm.timeline.timeline_items[0].content[0].innerText.split('Website: https://one-fm.com\nAddress:')[0];
            } else {
              description = frm.doc.description.replace(/(<([^>]+)>)/gi, "");
            }
            // action to perform if Yes is selected
            frappe.call({
                method: "one_fm.api.doc_methods.issue.log_pivotal_tracker", //dotted path to server method
                freeze_message: 'Logging story to Pivotal Tracker',
                args:{name:frm.doc.name, description:description},
                callback: function(r) {
                    // code snippet
                    if(r.message.status=='success'){
                      frappe.msgprint("Pivotal Tracker story created successfully");
                      frm.refresh();
                      frm.reload_doc();
                    }
                }
            })
        }, () => {
            // action to perform if No is selected
        }
      )
    }, 'Create')
  }
}


let add_pivotal_section = frm => {
  if(frappe.user.has_role('System Manager')
    && frm.doc.pivotal_tracker && !document.querySelector('#pivotal_tracker_span')){
    let el = `
    <span id="pivotal_tracker_span">Issue have been logged to Pivotal tracker</span><br>
    <a href="${frm.doc.pivotal_tracker}" class="btn btn-primary" target="_blank">Pivotal Tracker</a>
    `;
    frm.dashboard.add_section(el, __("Pivotal Tracker"))
  }
}




// ADD NEW WHATSA BUTTON NEXT TO NEW EMAIL
let set_whatsapp_reply_button = frm => {
  // check for whatsapp communication channel and number
  if(frm.doc.communication_medium=='WhatsApp' && frm.doc.whatsapp_number){
    if (!document.querySelector('#whatsapp-reply-btn')){
      let newMessageBTN = document.querySelector('.btn.btn-xs.btn-secondary-dark.action-btn');
      let el = document.createElement('button');
      el.className = `btn btn-xs btn-primary action-btn`;
      el.id = "whatsapp-reply-btn";
      el.innerHTML = `
      <i class="fa fa-whatsapp"></i>
      </svg>
      &nbsp;New WhatsApp`;
      newMessageBTN.parentNode.insertBefore(el, newMessageBTN.nextSibling);

      // add event listener to the button
      $('#whatsapp-reply-btn').click(() => {
        whatsappForm(frm);
      })
    }
  }
}

// whatsapp message form
let whatsappForm = (frm) => {
    let d = new frappe.ui.Dialog({
      title: 'Respond via WhatsApp',
      fields: [
          {
              label: 'Recipient',
              fieldname: 'recipient',
              fieldtype: 'Data',
              default: frm.doc.whatsapp_number.replace('whatsapp:', ''),
              read_only: 1
          },
          {
              label: 'Message',
              fieldname: 'message',
              fieldtype: 'Small Text',
              reqd: 1
          },
      ],
      primary_action_label: 'Send',
      primary_action(values) {
        values.doc = frm.doc.name
        frappe.call({
          method: "one_fm.api.doc_methods.issue.whatsapp_reply_issue",
          type: "POST",
          args: values,
          callback: function(r) {
            if(r.message){
              frappe.show_alert('WhatsApp Sent!', 5);
            }else{
              frappe.throw('An error occurred and have been reported!')
            }
            frm.reload_doc();
          },
          freeze: true,
          freeze_message: "Sending message to "+ values.recipient,
          async: true,
        });

          d.hide();
      }
  });

  d.show();
};
