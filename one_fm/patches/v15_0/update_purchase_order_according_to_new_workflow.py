import frappe


def execute():
    # Remove PO Approver Custom Field
    columns = ['custom_purchase_order_approver', 'custom_purchase_order_approver_name']
    for column in columns:
      if column in frappe.db.get_table_columns("Purchase Order"):
          frappe.db.sql("ALTER TABLE `tabPurchase Order` drop column {0}".format(column))

    # Update all PO in 'Pending Approver' to 'Pending Purchase Manager'
    frappe.db.sql(""" UPDATE `tabPurchase Order`
                    SET workflow_state = 'Pending Purchase Manager'
                    WHERE workflow_state = 'Pending Approver'
                  """)
    
    # Update all PO in 'Rejected' to 'Hold'
    frappe.db.sql(""" UPDATE `tabPurchase Order`
                  SET workflow_state = 'Hold', docstatus = 0
                  WHERE workflow_state = 'Rejected'
                  """)
    
    frappe.db.commit()