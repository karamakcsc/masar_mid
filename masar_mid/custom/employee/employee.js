frappe.ui.form.on('Employee', {
    custom_employee_salary_component: function(frm){
        frm.doc.custom_salary_component_table.forEach(function(row) {
            if (row.salary_component) {
                let same_components = frm.doc.custom_salary_component_table.filter(function(r) {
                    return r.salary_component === row.salary_component;
                });

                if (same_components.length > 1) {
                    let active_count = same_components.filter(function(r) {
                        return r.is_active;
                    }).length;

                    if (active_count > 1) {
                        frappe.throw(`Only one salary component: "${row.salary_component}" can be active.`);
                    }
                }
            }
        });
        frm.refresh_field('custom_employee_salary_component');
    },
    validate: function(frm) {
        frm.doc.custom_salary_component_table.forEach(function(row) {
            if (row.salary_component) {
                let same_components = frm.doc.custom_salary_component_table.filter(function(r) {
                    // frappe.msgprint(r.salary_component);
                    return r.salary_component === row.salary_component;
                });

                if (same_components.length > 1) {
                    let active_count = same_components.filter(function(r) {
                        // frappe.msgprint(r.is_active);
                        return r.is_active;
                    }).length;

                    if (active_count > 1) {
                        // frappe.msgprint(active_count);
                        frappe.throw(`Only one salary component: "${row.salary_component}" can be active.`);
                    }
                }
            }
        });
        frm.refresh_field('custom_employee_salary_component');
    }
});


//   frappe.ui.form.on("Employee", "onload", function(frm) {
//     frappe.msgprint("hi")
//     if (frappe.user_roles.includes("Employee Self Service")) {
//        {
//            var df=frappe.meta.get_docfield("Employee", "gender",frm.doc.name);
//            df.read_only=1;
//         //    var df=frappe.meta.get_docfield("Payment Entry", "payment_type",frm.doc.name);
//         //    df.read_only=1;
//         //    var df=frappe.meta.get_docfield("Payment Entry", "paid_to",frm.doc.name);
//         //    df.read_only=1;
//         //    var df=frappe.meta.get_docfield("Payment Entry", "party_type",frm.doc.name);
//         //    df.read_only=1;
//         //    var df=frappe.meta.get_docfield("Payment Entry", "mode_of_payment",frm.doc.name);
//         //    df.read_only=1;
//         //    var df=frappe.meta.get_docfield("Payment Entry", "posting_date",frm.doc.name);
//         //    df.read_only=1;
//         //    frm.set_value('naming_series', 'ACC-PAY-.YYYY.-')
//         //    frm.set_value('payment_type', 'Receive')
//         //    frm.set_value('mode_of_payment', 'Cash-قويزةلمعرض')
//         //    frm.set_value('paid_to', '111003 - صندوق المستودع (قويزة ) - SATC')
//         //    frm.set_value('party_type', 'Customer')
//            frm.refresh_fields();
//        }
//      }
//     });
  