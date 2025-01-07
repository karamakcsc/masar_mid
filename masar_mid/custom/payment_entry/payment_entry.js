frappe.ui.form.on('Payment Entry',  {
    validate: function(frm) {
        set_from_account(frm);
    },
    paid_from: function(frm) {
        set_from_account(frm);
    }
});


function set_from_account(frm) {
    if(frm.doc.mode_of_payment == "Cheque"){
        if(frm.doc.paid_from){
            let from_account = frm.doc.paid_from;
            if (frm.doc.payment_cheques){
                frm.doc.payment_cheques.forEach(function(row) {
                    frappe.model.set_value(row.doctype, row.name, "paid_from", from_account);
                    
                });
                frm.refresh_field('payment_cheques');
            }
        }
    }
}