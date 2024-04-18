// frappe.ui.form.on('Employee', {
//     onload: function(frm) {
//       // do something when the form is loaded
//     },
//     refresh: function(frm) {
//       // check if the current user is of type "Employee Self Service"
//       if (frappe.user_roles.includes("Employee Self Service")) {
//         // hide the dashboard
//         frm.toggle_display("gender", false);
//       }
//     }
//   });


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
  