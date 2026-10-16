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




// frappe.ui.form.on("Performance Task", {
//     setup(frm) {
//         // Dropdown link queries set karein
//         frm.set_query("department", () => {
//             return {
//                 query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_departments"
//             };
//         });

//         frm.set_query("assigned_by", () => {
//             return {
//                 query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_assigned_by"
//             };
//         });

//         frm.set_query("assigned_to", () => {
//             return {
//                 query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_assigned_to"
//             };
//         });
//     },

//     onload(frm) {
//         if (frm.is_new()) {
//             frappe.call({
//                 method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
//                 callback(r) {
//                     if (!r.message) return;
//                     const data = r.message;

//                     if (data.is_unrestricted) {
//                         frm.set_value("assigned_by", data.current_user);
//                         return;
//                     }

//                     if (data.department) {
//                         frm.set_value("department", data.department);
//                     }
//                     if (data.manager_user) {
//                         frm.set_value("assigned_by", data.manager_user);
//                     } else {
//                         frm.set_value("assigned_by", data.current_user);
//                     }
//                 }
//             });
//         }
//     },

//     department(frm) {
//         // Normal user agar department clear kare toh wapas auto-restore ho jaye
//         if (!frm.doc.department && !frappe.user.has_role("System Manager")) {
//             frappe.call({
//                 method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
//                 callback(r) {
//                     if (r.message && !r.message.is_unrestricted && r.message.department) {
//                         frm.set_value("department", r.message.department);
//                     }
//                 }
//             });
//         }
//     },

//     refresh(frm) {
//         frm.trigger("add_action_buttons");
//     },

//     add_action_buttons(frm) {
//         if (frm.is_new()) return;

//         const status = frm.doc.status;
//         const me = frappe.session.user;
//         const is_assignee = me === frm.doc.assigned_to;
//         const is_manager = frappe.user.has_role("System Manager") || frappe.user.has_role("HR Manager");

//         // Start Task — Pending → In Progress
//         if (status === "Pending" && is_assignee) {
//             frm.add_custom_button(__("Start Task"), () => {
//                 frm.set_value("status", "In Progress");
//                 frm.save().then(() => {
//                     frappe.show_alert({ message: "Task started!", indicator: "blue" });
//                 });
//             });
//         }

//         // In Progress actions
//         if (status === "In Progress" && is_assignee) {
//             if (frm.doc.requires_approval) {
//                 frm.add_custom_button(__("Submit for Approval"), () => {
//                     frm.set_value("status", "Pending Approval");
//                     frm.save().then(() => {
//                         frappe.show_alert({ message: "Submitted for approval.", indicator: "orange" });
//                     });
//                 }, __("Actions"));
//             } else {
//                 frm.add_custom_button(__("Mark Complete"), () => {
//                     frm.set_value("status", "Approved");
//                     frm.save().then(() => {
//                         frappe.show_alert({ message: "Task completed!", indicator: "green" });
//                     });
//                 }, __("Actions"));
//             }

//             if (frm.doc.task_type === "Delegation") {
//                 frm.add_custom_button(__("Request Extension"), () => {
//                     frappe.prompt([
//                         { label: "New Deadline", fieldname: "new_deadline", fieldtype: "Datetime", reqd: 1 },
//                         { label: "Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
//                     ], (values) => {
//                         frappe.call({
//                             method: "frappe.client.insert",
//                             args: {
//                                 doc: {
//                                     doctype: "Task Extension Request",
//                                     task: frm.doc.name,
//                                     requested_by: frappe.session.user,
//                                     current_deadline: frm.doc.deadline,
//                                     requested_deadline: values.new_deadline,
//                                     reason: values.reason
//                                 }
//                             },
//                             callback() {
//                                 frappe.show_alert({ message: "Extension request submitted!", indicator: "green" });
//                             }
//                         });
//                     }, __("Request Deadline Extension"));
//                 }, __("Actions"));
//             }
//         }

//         // Manager approval buttons
//         if (status === "Pending Approval" && is_manager) {
//             frm.add_custom_button(__("Approve"), () => {
//                 frappe.call({
//                     method: "performance_management.performance_management.doctype.performance_task.performance_task.approve_task",
//                     args: { task_name: frm.doc.name },
//                     callback() {
//                         frm.reload_doc();
//                         frappe.show_alert({ message: "Task Approved!", indicator: "green" });
//                     }
//                 });
//             }, __("Actions"));

//             frm.add_custom_button(__("Reject"), () => {
//                 frappe.prompt([
//                     { label: "Rejection Reason", fieldname: "reason", fieldtype: "Text", reqd: 1 }
//                 ], (values) => {
//                     frappe.call({
//                         method: "performance_management.performance_management.doctype.performance_task.performance_task.reject_task",
//                         args: { task_name: frm.doc.name, reason: values.reason },
//                         callback() {
//                             frm.reload_doc();
//                             frappe.show_alert({ message: "Task Rejected.", indicator: "orange" });
//                         }
//                     });
//                 });
//             }, __("Actions"));
//         }

//         // Reopened — allow restart
//         if (status === "Reopened" && is_assignee) {
//             frm.add_custom_button(__("Restart Task"), () => {
//                 frm.set_value("status", "In Progress");
//                 frm.save().then(() => {
//                     frappe.show_alert({ message: "Task restarted.", indicator: "blue" });
//                 });
//             });
//         }

//         // Overdue banner
//         if (frm.doc.is_overdue) {
//             frm.dashboard.set_headline_alert(
//                 '<span class="indicator red"></span> This task is <b>Overdue</b>',
//                 "red"
//             );
//         }
//     },

//     priority(frm) {
//         const needs_approval = ["High", "Critical"].includes(frm.doc.priority) || frm.doc.task_type === "Compliance";
//         frm.set_value("requires_approval", needs_approval ? 1 : 0);
//     },

//     task_type(frm) {
//         frm.trigger("priority");
//     }
// });



frappe.ui.form.on("Performance Task", {
    setup(frm) {
        // Link queries bind karein
        frm.set_query("department", () => {
            return {
                query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_departments"
            };
        });

        frm.set_query("assigned_by", () => {
            return {
                query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_assigned_by"
            };
        });

        frm.set_query("assigned_to", () => {
            return {
                query: "performance_management.performance_management.doctype.performance_task.performance_task.get_allowed_assigned_to"
            };
        });
    },

    onload(frm) {
        if (frm.is_new()) {
            frappe.call({
                method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
                callback(r) {
                    if (!r.message) return;
                    const data = r.message;

                    // Assigned by hamesha current logged in user se shuru hoga
                    frm.set_value("assigned_by", data.current_user);

                    // Agar user MD ya Founder Office nahi hai
                    if (!data.is_unrestricted) {
                        if (data.department) {
                            frm.set_value("department", data.department);
                        }
                        // Normal users ke liye Assigned By ko locked kar dein
                        frm.set_df_property("assigned_by", "read_only", 1);
                    }
                }
            });
        }
    },

    refresh(frm) {
        // Lock assigned_by for normal users
        frappe.call({
            method: "performance_management.performance_management.doctype.performance_task.performance_task.get_user_hierarchy_context",
            callback(r) {
                if (r.message && !r.message.is_unrestricted) {
                    frm.set_df_property("assigned_by", "read_only", 1);
                }
            }
        });

        frm.trigger("add_action_buttons");
    },

    add_action_buttons(frm) {
        if (frm.is_new()) return;

        const status = frm.doc.status;
        const me = frappe.session.user;
        const is_assignee = me === frm.doc.assigned_to;
        const is_manager = frappe.user.has_role("Managing Director") || frappe.user.has_role("Founder Office") || frappe.user.has_role("System Manager") || frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager") || frappe.user.has_role("Department Head");

        if (status === "Pending" && is_assignee) {
            frm.add_custom_button(__("Start Task"), () => {
                frm.set_value("status", "In Progress");
                frm.save().then(() => {
                    frappe.show_alert({ message: "Task started!", indicator: "blue" });
                });
            });
        }

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
                        frappe.db.get_value("User", frm.doc.assigned_to, "full_name", (r) => {
                            const requesterFullName = r && r.full_name ? r.full_name : frm.doc.assigned_to;
                        frappe.call({
                            method: "frappe.client.insert",
                            args: {
                                doc: {
                                    doctype: "Task Extension Request",
                                    task: frm.doc.name,
                                    requested_by: frappe.session.user,
                                    current_deadline: frm.doc.deadline,
                                    requested_deadline: values.new_deadline,
                                    requested_name: requesterFullName,
                                    reason: values.reason
                                }
                            },
                            callback() {
                                frappe.show_alert({ message: "Extension request submitted!", indicator: "green" });
                            }
                        });
                    });
                    }, __("Request Deadline Extension"));
                }, __("Actions"));
            }
        }

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

        if (status === "Reopened" && is_assignee) {
            frm.add_custom_button(__("Restart Task"), () => {
                frm.set_value("status", "In Progress");
                frm.save().then(() => {
                    frappe.show_alert({ message: "Task restarted.", indicator: "blue" });
                });
            });
        }

        if (frm.doc.is_overdue) {
            frm.dashboard.set_headline_alert(
                '<span class="indicator red"></span> This task is <b>Overdue</b>',
                "red"
            );
        }


        // Is code ko add_action_buttons function ke andar lagayein jahan manager actions hote hain
// Sirf tabhi dikhega jab task ka score 0 ho aur user assigner ho (ya top management)
// 'const me' ko dobara likhne ki zaroorat nahi hai, agar upar define hai toh seedha ye likhein:
// Top management aur assigner ka check JS ke mutabiq
const is_top_mgmt = frappe.user.has_role("Managing Director") || 
frappe.user.has_role("Founder Office") || 
frappe.user.has_role("System Manager") || 
frappe.user.has_role("Administrator");

const is_assigner = me === frm.doc.assigned_by || is_top_mgmt;
const is_score_zero = frm.doc.score === 0 || frm.doc.status === "Cancelled";

if (is_assigner && is_score_zero && frm.doc.status !== "Draft") {
frm.add_custom_button(__("Redelegate Task"), () => {
frappe.prompt([
{ label: "New Deadline", fieldname: "new_deadline", fieldtype: "Datetime", reqd: 1 },
// { label: "New Assignee", fieldname: "new_assignee", fieldtype: "Link", options: "User" }
], (values) => {
frappe.call({
method: "performance_management.performance_management.doctype.performance_task.performance_task.redelegate_task",
args: {
task_name: frm.doc.name,
new_deadline: values.new_deadline,
new_assignee: values.new_assignee
},
callback(r) {
if (r.message && r.message.status === "success") {
    frappe.show_alert({ message: "Task Redelegated Successfully!", indicator: "green" });
    frappe.set_route("Form", "Performance Task", r.message.new_task);
}
}
});
}, __("Redelegate Task"));
}, __("Actions"));
}

if (is_assignee && is_score_zero) {
frm.add_custom_button(__("Request for Redelegation"), () => {
frappe.prompt([
{ label: "Reason / Note for Manager", fieldname: "reason", fieldtype: "Text", reqd: 1 }
], (values) => {
frappe.call({
method: "performance_management.performance_management.doctype.performance_task.performance_task.request_redelegation",
args: {
task_name: frm.doc.name,
reason: values.reason
},
callback(r) {
if (r.message && r.message.status === "success") {
    frappe.show_alert({ message: "Redelegation request sent to manager!", indicator: "green" }, 5);
    frm.reload_doc();
}
}
});
}, __("Request Redelegation"));
}, __("Actions"));
}
    },

    priority(frm) {
        const needs_approval = ["High", "Critical"].includes(frm.doc.priority) || frm.doc.task_type === "Compliance";
        frm.set_value("requires_approval", needs_approval ? 1 : 0);
    },

    task_type(frm) {
        frm.trigger("priority");
    },

    assigned_to(frm) {
        if (!frm.doc.assigned_to) return;

        // Selected user ka department server se fetch karke auto-set karein
        frappe.call({
            method: "performance_management.performance_management.doctype.performance_task.performance_task.get_department_by_user",
            args: {
                user: frm.doc.assigned_to
            },
            callback(r) {
                if (r.message) {
                    frm.set_value("department", r.message);
                }
            }
        });
    },
});