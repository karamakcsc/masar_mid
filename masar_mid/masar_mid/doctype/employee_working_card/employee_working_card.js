// Copyright (c) 2023, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Working Card', {
	// refresh: function(frm) {

	// }
});
////// Fetching Employee with Filter ///// Start ///Siam
frappe.ui.form.on("Employee Working Card", "refresh", function(frm) {
    frm.fields_dict['working_days'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        //console.log(child);
        return {
            filters: {
                "is_group": 0
            }
        };
    };
});
////// Fetching Employee with Filter ///// END ///Siam

////// Calculate Total Work Hours  ///// Start ///Siam
frappe.ui.form.on('Employee Working Card Detail', {
    working_days_remove: function(frm, cdt, cdn) {
        update_total_day_work_hours(frm);
    },
    day_work_hours: function(frm, cdt, cdn) {
        update_total_day_work_hours(frm);
    },
});

function update_total_day_work_hours(frm) {
    var total = 0;
    frm.doc.working_days.forEach(function(d) {
        total += flt(d.day_work_hours);
    });
    frm.set_value('total_day_work_hours', total);
}
frappe.ui.form.on('Employee Working Card Detail', {
    working_days_remove: function(frm, cdt, cdn) {
        update_night_work_hours(frm);
    },
    night_work_hours: function(frm, cdt, cdn) {
        update_night_work_hours(frm);
    },
});

function update_night_work_hours(frm) {
    var total = 0;
    frm.doc.working_days.forEach(function(d) {
        total += flt(d.night_work_hours);
    });
    frm.set_value('total_night_work_hours', total);
}


frappe.ui.form.on('Employee Working Card Detail', {
    working_days_remove: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
    day_work_hours: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
    night_work_hours: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
});

function update_total_working_hours(frm) {
    var total = 0;
    frm.doc.working_days.forEach(function(d) {
        total += flt(d.night_work_hours + d.day_work_hours);
    });
    frm.set_value('total_working_hours', total);
}

frappe.ui.form.on('Employee Working Card Detail', {
    working_days_remove: function(frm, cdt, cdn) {
        update_total_overtime_hours(frm);
    },
    total_overtime: function(frm, cdt, cdn) {
        update_total_overtime_hours(frm);
    },
});

function update_total_overtime_hours(frm) {
    var total = 0;
    frm.doc.working_days.forEach(function(d) {
        total += flt(d.total_overtime);
    });
    frm.set_value('total_overtime_hours', total);
}
////// Calculate Total Work Hours  ///// END ///Siam

frappe.ui.form.on('Employee Working Card Detail', {
    working_days_remove: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
    day_work_hours: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
    night_work_hours: function(frm, cdt, cdn) {
        update_total_working_hours(frm);
    },
});

function update_total_working_hours(frm) {
    var total = 0;
    frm.doc.working_days.forEach(function(d) {
        total += flt(d.night_work_hours + d.day_work_hours);
    });
    d.total_working_hours = flt(d.night_work_hours * d.day_work_hours)
    cur_frm.refresh_field();
}























frappe.ui.form.on("Employee Working Card Detail", "rate", function(frm, cdt, cdn) {
		  var d = locals[cdt][cdn];
       if (d.item_code)  {
         if (d.price_list_rate > 0){
         d.amount_before_discount = flt(d.price_list_rate * d.qty)
         cur_frm.refresh_field();
       }
       else {
         d.amount_before_discount = flt(d.rate * d.qty)
         cur_frm.refresh_field();
       }
     }
});
