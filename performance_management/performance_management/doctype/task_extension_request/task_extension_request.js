// frappe.ui.form.on("Task Extension Request", {
// 	refresh(frm) {
// 		const is_manager = frappe.user.has_role("System Manager") || frappe.user.has_role("HR Manager")||frappe.user.has_role("Managing Director") || 
// 		frappe.user.has_role("Founder Office")|| 
// 		frappe.user.has_role("Department Head")||frappe.user.has_role("Task Extension Manager");

// 		if (frm.doc.approval_status === "Pending" && !frm.is_new() && is_manager) {
// 			frm.add_custom_button(__("Approve Extension"), () => {
// 				frappe.confirm(__("Are you sure you want to approve this extension request? This will automatically update the parent task's deadline."), () => {
// 					frappe.call({
// 						method: "performance_management.performance_management.doctype.task_extension_request.task_extension_request.approve_extension",
// 						args: { request_name: frm.doc.name },
// 						callback() {
// 							frm.reload_doc();
// 							frappe.show_alert({ message: "Extension Approved and Task Deadline Updated!", indicator: "green" });
// 						}
// 					});
// 				});
// 			}, __("Actions"));

// 			frm.add_custom_button(__("Reject Extension"), () => {
// 				frappe.prompt([
// 					{ label: "Rejection Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
// 				], (values) => {
// 					frappe.call({
// 						method: "performance_management.performance_management.doctype.task_extension_request.task_extension_request.reject_extension",
// 						args: { request_name: frm.doc.name, reason: values.reason },
// 						callback() {
// 							frm.reload_doc();
// 							frappe.show_alert({ message: "Extension Rejected.", indicator: "orange" });
// 						}
// 					});
// 				});
// 			}, __("Actions"));
// 		}

// 		// Disable form if not pending
// 		if (frm.doc.approval_status !== "Pending") {
// 			frm.disable_form();
// 		}
// 	}
// });



frappe.ui.form.on("Task Extension Request", {
    refresh(frm) {
        if (frm.doc.approval_status !== "Pending" || frm.is_new()) {
            if (frm.doc.approval_status !== "Pending") {
                frm.disable_form();
            }
            return;
        }

        const me = frappe.session.user;
        const has_role = frappe.user.has_role("System Manager") || 
                         frappe.user.has_role("HR Manager") || 
                         frappe.user.has_role("Managing Director") || 
                         frappe.user.has_role("Founder Office") || frappe.user.has_role("Department Head")||frappe.user.has_role("Task Extension Manager");

        // Server se check karenge ki kya yeh logged-in user hi is task ka assigned_by (manager) hai
        if (frm.doc.task) {
            frappe.db.get_value("Performance Task", frm.doc.task, "assigned_by", (r) => {
                const is_task_manager = r && r.assigned_by === me;

                // Agar user top management me hai YA phir wohi task ka manager hai
                if (has_role || is_task_manager) {
                    frm.add_custom_button(__("Approve Extension"), () => {
                        frappe.confirm(__("Are you sure you want to approve this extension request? This will automatically update the parent task's deadline."), () => {
                            frappe.call({
                                method: "performance_management.performance_management.doctype.task_extension_request.task_extension_request.approve_extension",
                                args: { request_name: frm.doc.name },
                                callback() {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: "Extension Approved and Task Deadline Updated!", indicator: "green" });
                                }
                            });
                        });
                    }, __("Actions"));

                    frm.add_custom_button(__("Reject Extension"), () => {
                        frappe.prompt([
                            { label: "Rejection Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
                        ], (values) => {
                            frappe.call({
                                method: "performance_management.performance_management.doctype.task_extension_request.task_extension_request.reject_extension",
                                args: { request_name: frm.doc.name, reason: values.reason },
                                callback() {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: "Extension Rejected.", indicator: "orange" });
                                }
                            });
                        });
                    }, __("Actions"));
                }
            });
        }
    }
});