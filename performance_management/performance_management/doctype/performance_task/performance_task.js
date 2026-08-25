// frappe.ui.form.on("Performance Task", {
// 	refresh(frm) {
// 		frm.trigger("add_action_buttons");
// 	},

// 	add_action_buttons(frm) {
// 		if (frm.is_new()) return;

// 		const status = frm.doc.status;
// 		const me = frappe.session.user;
// 		const is_assignee = me === frm.doc.assigned_to;
// 		const is_manager = frappe.user.has_role("System Manager") || frappe.user.has_role("HR Manager");

// 		// Start Task — Pending → In Progress
// 		if (status === "Pending" && is_assignee) {
// 			frm.add_custom_button(__("Start Task"), () => {
// 				frm.set_value("status", "In Progress");
// 				frm.save().then(() => {
// 					frappe.show_alert({ message: "Task started!", indicator: "blue" });
// 				});
// 			});
// 		}

// 		// In Progress actions
// 		if (status === "In Progress" && is_assignee) {
// 			if (frm.doc.requires_approval) {
// 				frm.add_custom_button(__("Submit for Approval"), () => {
// 					frm.set_value("status", "Pending Approval");
// 					frm.save().then(() => {
// 						frappe.show_alert({ message: "Submitted for approval.", indicator: "orange" });
// 					});
// 				}, __("Actions"));
// 			} else {
// 				frm.add_custom_button(__("Mark Complete"), () => {
// 					frm.set_value("status", "Approved");
// 					frm.save().then(() => {
// 						frappe.show_alert({ message: "Task completed!", indicator: "green" });
// 					});
// 				}, __("Actions"));
// 			}

// 			if (frm.doc.task_type === "Delegation") {
// 				frm.add_custom_button(__("Request Extension"), () => {
// 					frappe.prompt([
// 						{ label: "New Deadline", fieldname: "new_deadline", fieldtype: "Datetime", reqd: 1 },
// 						{ label: "Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
// 					], (values) => {
// 						frappe.call({
// 							method: "frappe.client.insert",
// 							args: {
// 								doc: {
// 									doctype: "Task Extension Request",
// 									task: frm.doc.name,
// 									requested_by: frappe.session.user,
// 									current_deadline: frm.doc.deadline,
// 									requested_deadline: values.new_deadline,
// 									reason: values.reason
// 								}
// 							},
// 							callback() {
// 								frappe.show_alert({ message: "Extension request submitted!", indicator: "green" });
// 							}
// 						});
// 					}, __("Request Deadline Extension"));
// 				}, __("Actions"));
// 			}
// 		}

// 		// Manager approval buttons
// 		if (status === "Pending Approval" && is_manager) {
// 			frm.add_custom_button(__("Approve"), () => {
// 				frappe.call({
// 					method: "performance_management.performance_management.doctype.performance_task.performance_task.approve_task",
// 					args: { task_name: frm.doc.name },
// 					callback() {
// 						frm.reload_doc();
// 						frappe.show_alert({ message: "Task Approved!", indicator: "green" });
// 					}
// 				});
// 			}, __("Actions"));

// 			frm.add_custom_button(__("Reject"), () => {
// 				frappe.prompt([
// 					{ label: "Rejection Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
// 				], (values) => {
// 					frappe.call({
// 						method: "performance_management.performance_management.doctype.performance_task.performance_task.reject_task",
// 						args: { task_name: frm.doc.name, reason: values.reason },
// 						callback() {
// 							frm.reload_doc();
// 							frappe.show_alert({ message: "Task Rejected.", indicator: "orange" });
// 						}
// 					});
// 				});
// 			}, __("Actions"));
// 		}

// 		// Reopened — allow restart
// 		if (status === "Reopened" && is_assignee) {
// 			frm.add_custom_button(__("Restart Task"), () => {
// 				frm.set_value("status", "In Progress");
// 				frm.save().then(() => {
// 					frappe.show_alert({ message: "Task restarted.", indicator: "blue" });
// 				});
// 			});
// 		}

// 		// Overdue banner
// 		if (frm.doc.is_overdue) {
// 			frm.dashboard.set_headline_alert(
// 				'<span class="indicator red"></span> This task is <b>Overdue</b>',
// 				"red"
// 			);
// 		}
// 	},

// 	priority(frm) {
// 		const needs_approval = ["High", "Critical"].includes(frm.doc.priority) || frm.doc.task_type === "Compliance";
// 		frm.set_value("requires_approval", needs_approval ? 1 : 0);
// 	},

// 	task_type(frm) {
// 		frm.trigger("priority");
// 	}
// });




frappe.ui.form.on("Performance Task", {
    setup(frm) {
        frm.trigger("apply_hierarchy_filters");
    },

    onload(frm) {
        if (frm.is_new()) {
            frappe.call({
                method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
                callback(r) {
                    if (!r.message || r.message.is_admin || r.message.error) return;

                    const data = r.message;

                    // 1. Department auto-set karein
                    if (data.department) {
                        frm.set_value("department", data.department);
                    }

                    // 2. Assigned By auto-set karein
                    if (data.manager_user) {
                        frm.set_value("assigned_by", data.manager_user);
                    } else {
                        frm.set_value("assigned_by", data.current_user);
                    }
                }
            });
        }
    },

    apply_hierarchy_filters(frm) {
        frappe.call({
            method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
            callback(r) {
                if (!r.message || r.message.is_admin || r.message.error) return;

                const data = r.message;

                // 1. Department Filter (User clear kare tab bhi sirf apna department hi dikhega)
                if (data.department) {
                    frm.set_query("department", () => {
                        return {
                            filters: {
                                "name": data.department
                            }
                        };
                    });
                }

                // 2. Assigned By Filter
                const allowed_assigned_by = [];
                if (data.manager_user) allowed_assigned_by.push(data.manager_user);
                allowed_assigned_by.push(data.current_user);

                frm.set_query("assigned_by", () => {
                    return {
                        filters: {
                            "name": ["in", allowed_assigned_by]
                        }
                    };
                });

                // 3. Assigned To Filter
                const allowed_assigned_to = [...data.subordinates, data.current_user];
                frm.set_query("assigned_to", () => {
                    return {
                        filters: {
                            "name": ["in", allowed_assigned_to]
                        }
                    };
                });
            }
        });
    },

    // Agar user field clear kar de toh wapas apna department auto-restore ho jaye
    department(frm) {
        if (!frm.doc.department && !frappe.user.has_role("System Manager")) {
            frappe.call({
                method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
                callback(r) {
                    if (r.message && r.message.department) {
                        frm.set_value("department", r.message.department);
                    }
                }
            });
        }
    },

    refresh(frm) {
        frm.trigger("add_action_buttons");
    },

    add_action_buttons(frm) {
        if (frm.is_new()) return;

        const status = frm.doc.status;
        const me = frappe.session.user;
        const is_assignee = me === frm.doc.assigned_to;
        const is_manager = frappe.user.has_role("System Manager") || frappe.user.has_role("HR Manager");

        // Start Task — Pending → In Progress
        if (status === "Pending" && is_assignee) {
            frm.add_custom_button(__("Start Task"), () => {
                frm.set_value("status", "In Progress");
                frm.save().then(() => {
                    frappe.show_alert({ message: "Task started!", indicator: "blue" });
                });
            });
        }

        // In Progress actions
        if (status === "In Progress" && is_assignee) {
            if (frm.doc.requires_approval) {
                frm.add_custom_button(__("Submit for Approval"), () => {
                    frm.set_value("status", "Pending Approval");
                    frm.save().then(() => {
                        frappe.show_alert({ message: "Submitted for approval.", indicator: "orange" });
                    });
                }, __("Actions"));
            } else {
                frm.add_custom_button(__("Mark Complete"), () => {
                    frm.set_value("status", "Approved");
                    frm.save().then(() => {
                        frappe.show_alert({ message: "Task completed!", indicator: "green" });
                    });
                }, __("Actions"));
            }

            if (frm.doc.task_type === "Delegation") {
                frm.add_custom_button(__("Request Extension"), () => {
                    frappe.prompt([
                        { label: "New Deadline", fieldname: "new_deadline", fieldtype: "Datetime", reqd: 1 },
                        { label: "Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
                    ], (values) => {
                        frappe.call({
                            method: "frappe.client.insert",
                            args: {
                                doc: {
                                    doctype: "Task Extension Request",
                                    task: frm.doc.name,
                                    requested_by: frappe.session.user,
                                    current_deadline: frm.doc.deadline,
                                    requested_deadline: values.new_deadline,
                                    reason: values.reason
                                }
                            },
                            callback() {
                                frappe.show_alert({ message: "Extension request submitted!", indicator: "green" });
                            }
                        });
                    }, __("Request Deadline Extension"));
                }, __("Actions"));
            }
        }

        // Manager approval buttons
        if (status === "Pending Approval" && is_manager) {
            frm.add_custom_button(__("Approve"), () => {
                frappe.call({
                    method: "performance_management.performance_management.doctype.performance_task.performance_task.approve_task",
                    args: { task_name: frm.doc.name },
                    callback() {
                        frm.reload_doc();
                        frappe.show_alert({ message: "Task Approved!", indicator: "green" });
                    }
                });
            }, __("Actions"));

            frm.add_custom_button(__("Reject"), () => {
                frappe.prompt([
                    { label: "Rejection Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
                ], (values) => {
                    frappe.call({
                        method: "performance_management.performance_management.doctype.performance_task.performance_task.reject_task",
                        args: { task_name: frm.doc.name, reason: values.reason },
                        callback() {
                            frm.reload_doc();
                            frappe.show_alert({ message: "Task Rejected.", indicator: "orange" });
                        }
                    });
                });
            }, __("Actions"));
        }

        // Reopened — allow restart
        if (status === "Reopened" && is_assignee) {
            frm.add_custom_button(__("Restart Task"), () => {
                frm.set_value("status", "In Progress");
                frm.save().then(() => {
                    frappe.show_alert({ message: "Task restarted.", indicator: "blue" });
                });
            });
        }

        // Overdue banner
        if (frm.doc.is_overdue) {
            frm.dashboard.set_headline_alert(
                '<span class="indicator red"></span> This task is <b>Overdue</b>',
                "red"
            );
        }
    },

    priority(frm) {
        const needs_approval = ["High", "Critical"].includes(frm.doc.priority) || frm.doc.task_type === "Compliance";
        frm.set_value("requires_approval", needs_approval ? 1 : 0);
    },

    task_type(frm) {
        frm.trigger("priority");
    }
});