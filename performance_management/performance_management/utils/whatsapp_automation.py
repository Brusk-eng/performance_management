# import frappe
# from frappe.utils import today
# from performance_management.performance_management.utils.whatsapp import send_whatsapp_message

# def send_daily_whatsapp_reminders():
# 	"""
# 	Daily job: Send WhatsApp reminder to each user
# 	with pending/in-progress tasks due today or already overdue.
# 	"""
# 	today_str = today()
# 	tasks = frappe.db.sql("""
# 		SELECT assigned_to, name, task_title, deadline, is_overdue, task_type
# 		FROM `tabPerformance Task`
# 		WHERE status IN ('Pending', 'In Progress')
# 		AND DATE(deadline) <= %s
# 	""", today_str, as_dict=True)

# 	if not tasks:
# 		return

# 	# Group by user
# 	from collections import defaultdict
# 	user_tasks = defaultdict(list)
# 	for t in tasks:
# 		user_tasks[t.assigned_to].append(t)

# 	for user, user_task_list in user_tasks.items():
# 		try:
# 			send_reminder_whatsapp(user, user_task_list)
# 		except Exception as e:
# 			frappe.log_error(f"WhatsApp Reminder failed for {user}: {str(e)}", "WhatsApp Automation")


# def send_reminder_whatsapp(user, tasks):
# 	fields = ["name", "cell_number", "employee_name"]
# 	if frappe.db.has_column("Employee", "custom_company_phone_no"):
# 		fields.append("custom_company_phone_no")

# 	employee = frappe.db.get_value("Employee", {"user_id": user}, fields, as_dict=True)
	
# 	if not employee:
# 		# User doesn't have an associated employee record
# 		return

# 	mobile_no = employee.get("custom_company_phone_no") or employee.get("cell_number")
# 	if not mobile_no:
# 		# Employee doesn't have a mobile number configured
# 		return

# 	overdue_tasks = [t for t in tasks if t.is_overdue]
# 	checklist_tasks = [t for t in tasks if not t.is_overdue and t.task_type == "Checklist"]
# 	other_tasks = [t for t in tasks if not t.is_overdue and t.task_type != "Checklist"]
	
# 	# Build WhatsApp Message Text
# 	message = f"Hi {employee.employee_name},\n\n"
# 	message += f"📋 *Your Daily Task Summary*\n"
# 	message += f"You have {len(tasks)} tasks requiring your attention:\n\n"
	
# 	if overdue_tasks:
# 		message += "🚨 *OVERDUE TASKS*\n"
# 		for t in overdue_tasks:
# 			message += f"• *{t.task_title}* (Due: {t.deadline})\n"
# 		message += "\n"
		
# 	if checklist_tasks:
# 		message += "✅ *DAILY CHECKLIST*\n"
# 		for t in checklist_tasks:
# 			message += f"• *{t.task_title}*\n"
# 		message += "\n"
		
# 	if other_tasks:
# 		message += "📝 *STANDARD TASKS DUE TODAY*\n"
# 		for t in other_tasks:
# 			message += f"• *{t.task_title}*\n"
# 		message += "\n"
		
# 	message += "Please log in to your Workspace and update your task statuses.\n"
# 	message += "Have a great day!"

# 	# Send via Green API
# 	send_whatsapp_message(employee.name, mobile_no, message)




import frappe
from frappe.utils import today, format_datetime
from performance_management.performance_management.utils.whatsapp import send_whatsapp_message


def send_daily_whatsapp_reminders():
    """
    Daily job: Send WhatsApp reminder to each user
    with pending/in-progress/reopened tasks due today or already overdue.
    """
    today_str = today()
    tasks = frappe.db.sql("""
        SELECT assigned_to, name, task_title, deadline, is_overdue, task_type, score, extension_count
        FROM `tabPerformance Task`
        WHERE status IN ('Pending', 'In Progress', 'Reopened')
        AND DATE(deadline) <= %s
        ORDER BY deadline ASC
    """, today_str, as_dict=True)

    if not tasks:
        return

    from collections import defaultdict
    user_tasks = defaultdict(list)
    for t in tasks:
        user_tasks[t.assigned_to].append(t)

    for user, user_task_list in user_tasks.items():
        try:
            send_reminder_whatsapp(user, user_task_list)
        except Exception as e:
            frappe.log_error(f"WhatsApp Reminder failed for {user}: {str(e)}", "WhatsApp Automation")


def send_reminder_whatsapp(user, tasks):
    fields = ["name", "cell_number", "employee_name"]
    if frappe.db.has_column("Employee", "custom_company_phone_no"):
        fields.append("custom_company_phone_no")

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        fields,
        as_dict=True
    ) or frappe.db.get_value(
        "Employee",
        {"company_email": user, "status": "Active"},
        fields,
        as_dict=True
    )

    if not employee:
        return

    mobile_no = employee.get("custom_company_phone_no") or employee.get("cell_number")
    if not mobile_no:
        return

    overdue_tasks = [t for t in tasks if t.is_overdue or (t.extension_count and t.extension_count > 0)]
    checklist_tasks = [t for t in tasks if not t.is_overdue and not t.extension_count and t.task_type == "Checklist"]
    other_tasks = [t for t in tasks if not t.is_overdue and not t.extension_count and t.task_type != "Checklist"]

    message = f"Hi *{employee.employee_name}*,\n\n"
    message += f"📋 *Your Daily Task Summary*\n"
    message += f"You have {len(tasks)} tasks requiring your attention:\n\n"

    if overdue_tasks:
        message += "🚨 *OVERDUE / EXTENDED TASKS*\n"
        for t in overdue_tasks:
            deadline_str = format_datetime(t.deadline, "dd-MM-yyyy HH:mm") if t.deadline else "No Deadline"
            score_val = t.score if t.score is not None else 100.0
            ext_count = t.extension_count or 0

            if score_val <= 25.0:
                message += f"⚠️ *{t.task_title}* [ID: {t.name}]\n"
                message += f"   • *CRITICAL:* Current Score is *{int(score_val)}*\n"
            else:
                message += f"• *{t.task_title}* [ID: {t.name}]\n"
                message += f"   • Current Score: *{int(score_val)}*\n"

            message += f"   • Auto Extended: *{ext_count} time(s)* (+48 hrs each)\n"
            message += f"   • Deadline: {deadline_str}\n\n"

    if checklist_tasks:
        message += "✅ *DAILY CHECKLIST*\n"
        for t in checklist_tasks:
            message += f"• *{t.task_title}* [ID: {t.name}]\n"
        message += "\n"

    if other_tasks:
        message += "📝 *STANDARD TASKS DUE TODAY*\n"
        for t in other_tasks:
            deadline_str = format_datetime(t.deadline, "dd-MM-yyyy HH:mm") if t.deadline else "Today"
            message += f"• *{t.task_title}* [ID: {t.name}] (Due: {deadline_str})\n"
        message += "\n"

    message += "Please log in to your Workspace and update your task statuses.\n"
    message += "Have a great day!"

    send_whatsapp_message(employee.name, mobile_no, message)


def send_task_critical_score_alert(task_doc):
    """
    Direct WhatsApp alert trigger when a task score drops to <= 25 points (-25 per 48-hr extension).
    """
    if not task_doc.assigned_to:
        return

    fields = ["name", "cell_number", "employee_name"]
    if frappe.db.has_column("Employee", "custom_company_phone_no"):
        fields.append("custom_company_phone_no")

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": task_doc.assigned_to, "status": "Active"},
        fields,
        as_dict=True
    ) or frappe.db.get_value(
        "Employee",
        {"company_email": task_doc.assigned_to, "status": "Active"},
        fields,
        as_dict=True
    )

    if not employee:
        return

    mobile_no = employee.get("custom_company_phone_no") or employee.get("cell_number")
    if not mobile_no:
        return

    deadline_str = format_datetime(task_doc.deadline, "dd-MM-yyyy HH:mm") if task_doc.deadline else "N/A"

    msg = (
        f"⚠️ *CRITICAL TASK OVERDUE ALERT* ⚠️\n\n"
        f"Hi *{employee.employee_name}*,\n"
        f"Your task is overdue and your current score has dropped to *{int(task_doc.score)}* (-25 per 48-hr extension).\n\n"
        f"📌 *Task Details:*\n"
        f"• Task ID: *{task_doc.name}*\n"
        f"• Title: *{task_doc.task_title}*\n"
        f"• Total Auto Extensions: *{task_doc.extension_count} time(s)*\n"
        f"• Current Score: *{task_doc.score} / 100*\n"
        f"• Extended Deadline (+48 hrs): *{deadline_str}*\n\n"
        f"Please complete and submit this task immediately to prevent further score deduction."
    )

    send_whatsapp_message(employee.name, mobile_no, msg)