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
    }
});
