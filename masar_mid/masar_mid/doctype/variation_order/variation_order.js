// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Variation Order", {
	validate: function (frm) {
        calculate_totals(frm);
        frm.doc.update_items.forEach(function(row) {
            row.schedule_date = frm.doc.schedule_date;
        });
        frm.refresh_field('update_items');
    }, 
    qty: function(frm){
        calculate_totals(frm);
    },
    rate: function(frm){
        calculate_totals(frm);
    },
    refresh: function(frm){
        if(frm.doc.__islocal != 1 && frm.doc.docstatus === 0) { 
            frm.add_custom_button(__('Get Items'), function() {
                frappe.call({
                    doc: frm.doc,
                    method: "fetch_child_items",
                    callback: function(r) {
                        frm.refresh_field("current_items");
                        frm.refresh_field("update_items");
                        frm.refresh_field("total_qty");
                        frm.refresh_field("total");
                    }
                });
            });
        }
    }
});

frappe.ui.form.on('Variation Order Update Items', {
    qty: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        row.amount = row.qty * row.rate;
        frm.refresh_field('update_items');
    },
    rate: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        row.amount = row.qty * row.rate;
        frm.refresh_field('update_items');
    }
});


function calculate_totals(frm) {
    var total_qty = 0;
    var total_amount = 0;

    $.each(frm.doc.update_items || [], function(i, row) {
        total_qty += row.qty;
        total_amount += row.amount;
    });

    frm.set_value("upd_total_qty", total_qty);
    frm.set_value("upd_total", total_amount);

    frm.refresh_field("upd_total_qty");
    frm.refresh_field("upd_total");
}
//