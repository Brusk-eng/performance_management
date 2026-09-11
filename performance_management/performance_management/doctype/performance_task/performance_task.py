# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import now_datetime, get_datetime
# from performance_management.performance_management.utils.whatsapp import send_dual_notification


# VALID_STATUSES = ["Draft", "Pending", "In Progress", "Pending Approval", "Approved", "Reopened", "Cancelled"]


# class PerformanceTask(Document):

# 	def validate(self):
# 		self._set_assigned_by()
# 		self._set_approval_requirement()
# 		self._check_overdue()

# 	def before_save(self):
# 		self._handle_completion()
		
# 	def after_insert(self):
# 		if not self.flags.ignore_assignment_email:
# 			self._send_assignment_email()

# 	def on_update(self):
# 		if self.has_value_changed("status") and self.status == "Pending Approval":
# 			self._send_submission_email()
# 		self._log_audit("Update")

# 	# ── Internal helpers ──────────────────────────────────────────────────────

# 	def _set_assigned_by(self):
# 		if not self.assigned_by:
# 			emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["reports_to"], as_dict=True)
# 			if emp and emp.reports_to:
# 				manager_user = frappe.db.get_value("Employee", emp.reports_to, "user_id")
# 				self.assigned_by = manager_user or frappe.session.user
# 			else:	
# 				self.assigned_by = frappe.session.user
# 	def _set_approval_requirement(self):
# 		"""Auto-check 'Requires Approval' for High/Critical/Compliance tasks."""
# 		if self.priority in ("High", "Critical") or self.task_type == "Compliance":
# 			self.requires_approval = 1

# 	def _check_overdue(self):
# 		if self.deadline and self.status not in ("Approved", "Cancelled"):
# 			self.is_overdue = 1 if get_datetime(self.deadline) < now_datetime() else 0

# 	def _handle_completion(self):
# 		"""When marked Approved, set completion date and calculate score."""
# 		if self.status == "Approved" and not self.completion_date:
# 			self.completion_date = now_datetime()
# 			self._calculate_score()
# 		if self.status == "Reopened":
# 			self.score = max(0.0, (self.score or 100.0) - 20.0)

# 	def _calculate_score(self):
# 		base = 100.0
# 		base -= (self.extension_count or 0) * 20.0
# 		if self.deadline and self.completion_date:
# 			delay = (get_datetime(self.completion_date) - get_datetime(self.deadline)).days
# 			if delay > 0:
# 				base -= min(delay * 10, 50)
# 		self.score = max(0.0, base)

# 	def _log_audit(self, action):
# 		try:
# 			frappe.get_doc({
# 				"doctype": "PM Audit Log",
# 				"reference_doctype": self.doctype,
# 				"reference_name": self.name,
# 				"action": action,
# 				"user": frappe.session.user,
# 				"timestamp": now_datetime(),
# 				"details": f"Status: {self.status} | Priority: {self.priority}"
# 			}).insert(ignore_permissions=True)
# 		except Exception:
# 			pass  # Never let logging break the main flow

# 	def _send_assignment_email(self):
# 		if self.assigned_to:
# 			msg = f"<p>Hello,</p><p>You have been assigned a new task: <strong>{self.task_title}</strong>.</p><p>Priority: <b>{self.priority}</b><br>Deadline: <b>{self.deadline or 'None'}</b></p>"
# 			wa_msg = f"You have been assigned a new task: *{self.task_title}*.\nPriority: *{self.priority}*\nDeadline: *{self.deadline or 'None'}*"
# 			send_dual_notification(self.assigned_to, f"New Task Assigned: {self.task_title}", msg, wa_msg)

# 	def _send_submission_email(self):
# 		if self.assigned_by:
# 			msg = f"<p>Hello,</p><p><strong>{self.assigned_to}</strong> has submitted the task <strong>{self.task_title}</strong> for your approval.</p>"
# 			wa_msg = f"*{self.assigned_to}* has submitted the task *{self.task_title}* for your approval."
# 			send_dual_notification(self.assigned_by, f"Task Pending Approval: {self.task_title}", msg, wa_msg)

# 	def _send_decision_email(self, decision, reason=None):
# 		if self.assigned_to:
# 			reason_html = f"<p>Manager Comments: {reason}</p>" if reason else ""
# 			reason_wa = f"\nManager Comments: {reason}" if reason else ""
# 			color = "green" if decision == "Approved" else "red"
# 			msg = f"<p>Hello,</p><p>Your task <strong>{self.task_title}</strong> has been <b><span style='color:{color}'>{decision}</span></b>.</p>{reason_html}"
# 			wa_msg = f"Your task *{self.task_title}* has been *{decision}*.{reason_wa}"
# 			send_dual_notification(self.assigned_to, f"Task {decision}: {self.task_title}", msg, wa_msg)

# 	# ── Whitelisted APIs ──────────────────────────────────────────────────────

# @frappe.whitelist()
# def approve_task(task_name):
# 	"""Manager approves a task — sets Approved status directly."""
# 	task = frappe.get_doc("Performance Task", task_name)
# 	if task.status != "Pending Approval":
# 		frappe.throw(_("Task must be in 'Pending Approval' status to approve."))
# 	task.status = "Approved"
# 	task.approved_by = frappe.session.user
# 	task.approval_status = "Approved"
# 	task.save(ignore_permissions=True)
# 	task._send_decision_email("Approved")
# 	return {"status": "approved", "score": task.score}


# @frappe.whitelist()
# def reject_task(task_name, reason):
# 	"""Manager rejects — moves task to Reopened."""
# 	task = frappe.get_doc("Performance Task", task_name)
# 	if task.status != "Pending Approval":
# 		frappe.throw(_("Task must be in 'Pending Approval' status to reject."))
# 	task.status = "Reopened"
# 	task.rejection_reason = reason
# 	task.approval_status = "Rejected"
# 	task.save(ignore_permissions=True)
# 	task._send_decision_email("Rejected", reason)
# 	return {"status": "rejected"}


# @frappe.whitelist()
# def get_my_tasks(user=None):
# 	"""Returns open tasks for the current user (for dashboard)."""
# 	user = user or frappe.session.user
# 	return frappe.get_all(
# 		"Performance Task",
# 		filters={"assigned_to": user, "status": ["not in", ["Approved", "Cancelled"]]},
# 		fields=["name", "task_title", "status", "priority", "deadline", "is_overdue"],
# 		order_by="deadline asc"
# 	)


# @frappe.whitelist()
# def generate_tasks_from_template(template_name, assigned_to, deadline):
# 	"""Bulk create Performance Tasks from a Checklist Template."""
# 	template = frappe.get_doc("Checklist Template", template_name)
# 	created = []
# 	for item in template.items:
# 		task = frappe.get_doc({
# 			"doctype": "Performance Task",
# 			"task_title": item.item_title,
# 			"description": item.description or "",
# 			"task_type": template.task_type,
# 			"priority": template.default_priority,
# 			"department": template.department,
# 			"assigned_to": assigned_to,
# 			"assigned_by": frappe.session.user,
# 			"deadline": deadline,
# 			"checklist_template": template_name,
# 			"frequency": template.frequency,
# 			"status": "Pending"
# 		})
# 		task.flags.ignore_assignment_email = True
# 		task.insert(ignore_permissions=True)
# 		created.append(task.name)
# 	return {"created": created, "count": len(created)}


# def get_permission_query_conditions(user):
# 	if not user:
# 		user = frappe.session.user
# 	if user == "Administrator":
# 		return ""
# 	return f"(`tabPerformance Task`.assigned_to = '{frappe.db.escape(user)}' OR `tabPerformance Task`.assigned_by = '{frappe.db.escape(user)}')"


# def has_permission(doc, ptype="read", user=None):
# 	if not user:
# 		user = frappe.session.user
# 	if user == "Administrator":
# 		return True
# 	if doc.assigned_to == user or doc.assigned_by == user:
# 		return True
# 	return False



# def is_super_user(user):
#     """Check if the user is Administrator or has System Manager role."""
#     if user == "Administrator":
#         return True
#     return "System Manager" in frappe.get_roles(user)


# @frappe.whitelist()
# def get_user_hierarchy_context():
#     """Logged in user ka Employee context: Department, Reporting Manager, aur Direct Subordinates fetch karega."""
#     user = frappe.session.user

#     # Administrator & System Manager unrestricted hain
#     if is_super_user(user):
#         return {"is_unrestricted": True, "current_user": user}

#     # User ka Active Employee record dhoondein
#     employee = frappe.db.sql("""
#         SELECT name, department, reports_to 
#         FROM `tabEmployee` 
#         WHERE (user_id = %s OR company_email = %s OR prefered_email = %s)
#           AND status = 'Active'
#         LIMIT 1
#     """, (user, user, user), as_dict=True)

#     if not employee:
#         return {"is_unrestricted": False, "department": None, "manager_user": None, "current_user": user}

#     emp = employee[0]
#     manager_user_id = None
#     if emp.reports_to:
#         manager_user_id = frappe.db.get_value("Employee", emp.reports_to, "user_id")

#     return {
#         "is_unrestricted": False,
#         "department": emp.department,
#         "manager_user": manager_user_id or user,
#         "current_user": user
#     }


# # ─── Custom Query Handlers (Server Side Dropdowns) ───────────────────────────

# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_departments(doctype, txt, searchfield, start, page_len, filters):
#     """Department dropdown: System Managers ko sabhi, baaki sabhi ko sirf apna department."""
#     user = frappe.session.user
#     if is_super_user(user):
#         return frappe.db.sql("""
#             SELECT name, department_name FROM `tabDepartment`
#             WHERE name LIKE %(txt)s
#             ORDER BY name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     emp = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, ["department"], as_dict=True)
#     if emp and emp.department:
#         return [[emp.department, emp.department]]
#     return []


# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_assigned_by(doctype, txt, searchfield, start, page_len, filters):
#     """Assigned By dropdown: Normal user ko sirf unka Manager aur wo khud."""
#     user = frappe.session.user
#     if is_super_user(user):
#         return frappe.db.sql("""
#             SELECT name, full_name FROM `tabUser`
#             WHERE enabled = 1 AND user_type = 'System User' AND (name LIKE %(txt)s OR full_name LIKE %(txt)s)
#             ORDER BY name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     allowed_users = [user]
#     emp = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, ["reports_to"], as_dict=True)
#     if emp and emp.reports_to:
#         mgr_user = frappe.db.get_value("Employee", emp.reports_to, "user_id")
#         if mgr_user:
#             allowed_users.append(mgr_user)

#     return frappe.db.sql("""
#         SELECT name, full_name FROM `tabUser`
#         WHERE name IN %(users)s AND enabled = 1
#         ORDER BY name ASC
#     """, {"users": tuple(allowed_users)})


# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_assigned_to(doctype, txt, searchfield, start, page_len, filters):
#     """Assigned To dropdown: Normal user ko sirf uske Direct Subordinates aur wo khud."""
#     user = frappe.session.user
#     if is_super_user(user):
#         return frappe.db.sql("""
#             SELECT name, full_name FROM `tabUser`
#             WHERE enabled = 1 AND user_type = 'System User' AND (name LIKE %(txt)s OR full_name LIKE %(txt)s)
#             ORDER BY name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     allowed_users = [user]
#     emp = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, ["name"], as_dict=True)
#     if emp:
#         subs = frappe.get_all("Employee", filters={"reports_to": emp.name, "status": "Active"}, pluck="user_id")
#         allowed_users.extend([s for s in subs if s])

#     return frappe.db.sql("""
#         SELECT name, full_name FROM `tabUser`
#         WHERE name IN %(users)s AND enabled = 1
#         ORDER BY name ASC
#     """, {"users": tuple(allowed_users)})


# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import now_datetime, get_datetime
# from performance_management.performance_management.utils.whatsapp import send_dual_notification

# VALID_STATUSES = ["Draft", "Pending", "In Progress", "Pending Approval", "Approved", "Reopened", "Cancelled"]

# # Full Access Roles jo puri company me kisi ko bhi task assign kar sakte hain
# TOP_MANAGEMENT_ROLES = ["Managing Director", "Founder Office", "Administrator", "System Manager"]


# class PerformanceTask(Document):

#     def validate(self):
#         if self.assigned_to:
#             dept = get_department_by_user(self.assigned_to)
#             if dept:
#                 self.department = dept
#         # Normal user ke liye assigned_by hamesha logged-in user hi rahega
#         if not is_top_management(frappe.session.user) or not self.assigned_by:
#             self.assigned_by = frappe.session.user

#         # Hierarchy validation
#         self._validate_assigned_to_hierarchy()
#         self._set_approval_requirement()
#         self._check_overdue()

#     def before_save(self):
#         self._handle_completion()

#     def after_insert(self):
#         if not self.flags.ignore_assignment_email:
#             self._send_assignment_email()

#     def on_update(self):
#         if self.has_value_changed("status") and self.status == "Pending Approval":
#             self._send_submission_email()
#         self._log_audit("Update")

#     # ── Internal helpers ──────────────────────────────────────────────────────

#     def _validate_assigned_to_hierarchy(self):
#         user = frappe.session.user
#         if not self.assigned_to or is_top_management(user):
#             return

#         allowed = [u.lower() for u in get_allowed_assignee_users(user)]
#         if self.assigned_to.strip().lower() not in allowed:
#             frappe.throw(
#                 _("Aap <b>{0}</b> ko task assign nahi kar sakte. Aap sirf apni direct team aur peers ko assign kar sakte hain.")
#                 .format(self.assigned_to)
#             )

#     def _set_approval_requirement(self):
#         if self.priority in ("High", "Critical") or self.task_type == "Compliance":
#             self.requires_approval = 1

#     def _check_overdue(self):
#         if self.deadline and self.status not in ("Approved", "Cancelled"):
#             self.is_overdue = 1 if get_datetime(self.deadline) < now_datetime() else 0

#     def _handle_completion(self):
#         if self.status == "Approved" and not self.completion_date:
#             self.completion_date = now_datetime()
#             self._calculate_score()
#         if self.status == "Reopened":
#             self.score = max(0.0, (self.score or 100.0) - 20.0)

#     def _calculate_score(self):
#         base = 100.0
#         base -= (self.extension_count or 0) * 20.0
#         if self.deadline and self.completion_date:
#             delay = (get_datetime(self.completion_date) - get_datetime(self.deadline)).days
#             if delay > 0:
#                 base -= min(delay * 10, 50)
#         self.score = max(0.0, base)

#     def _log_audit(self, action):
#         try:
#             frappe.get_doc({
#                 "doctype": "PM Audit Log",
#                 "reference_doctype": self.doctype,
#                 "reference_name": self.name,
#                 "action": action,
#                 "user": frappe.session.user,
#                 "timestamp": now_datetime(),
#                 "details": f"Status: {self.status} | Priority: {self.priority}"
#             }).insert(ignore_permissions=True)
#         except Exception:
#             pass

#     def _send_assignment_email(self):
#         if self.assigned_to:
#             msg = f"<p>Hello,</p><p>You have been assigned a new task: <strong>{self.task_title}</strong>.</p><p>Priority: <b>{self.priority}</b><br>Deadline: <b>{self.deadline or 'None'}</b></p>"
#             wa_msg = f"You have been assigned a new task: *{self.task_title}*.\nPriority: *{self.priority}*\nDeadline: *{self.deadline or 'None'}*"
#             send_dual_notification(self.assigned_to, f"New Task Assigned: {self.task_title}", msg, wa_msg)

#     def _send_submission_email(self):
#         if self.assigned_by:
#             msg = f"<p>Hello,</p><p><strong>{self.assigned_to}</strong> has submitted the task <strong>{self.task_title}</strong> for your approval.</p>"
#             wa_msg = f"*{self.assigned_to}* has submitted the task *{self.task_title}* for your approval."
#             send_dual_notification(self.assigned_by, f"Task Pending Approval: {self.task_title}", msg, wa_msg)

#     def _send_decision_email(self, decision, reason=None):
#         if self.assigned_to:
#             reason_html = f"<p>Manager Comments: {reason}</p>" if reason else ""
#             reason_wa = f"\nManager Comments: {reason}" if reason else ""
#             color = "green" if decision == "Approved" else "red"
#             msg = f"<p>Hello,</p><p>Your task <strong>{self.task_title}</strong> has been <b><span style='color:{color}'>{decision}</span></b>.</p>{reason_html}"
#             wa_msg = f"Your task *{self.task_title}* has been *{decision}*.{reason_wa}"
#             send_dual_notification(self.assigned_to, f"Task {decision}: {self.task_title}", msg, wa_msg)


# # ─── Hierarchy & Role Helpers ────────────────────────────────────────────────

# def is_top_management(user):
#     """Checks strictly if user has Managing Director, Founder Office, or Admin roles."""
#     if user == "Administrator":
#         return True
#     user_roles = frappe.get_roles(user)
#     return any(role in user_roles for role in TOP_MANAGEMENT_ROLES)


# def get_employee_by_user(user):
#     """Fetches active employee linked to user."""
#     emp = frappe.db.sql("""
#         SELECT name, reports_to, department, user_id, employee_name
#         FROM `tabEmployee`
#         WHERE (user_id = %s OR company_email = %s OR prefered_email = %s)
#           AND status = 'Active'
#         LIMIT 1
#     """, (user, user, user), as_dict=True)
#     return emp[0] if emp else None


# def get_allowed_assignee_users(user):
#     """
#     STRICT DOWNWARD ONLY:
#     - Normal user/manager sirf apne DIRECT SUBORDINATES (reports_to = current employee) 
#       aur KHUD (Self) ko hi task assign kar sakta hai.
#     - Peers (jaise Anurag, Virendra, Mayur) bilkul allow nahi honge.
#     """
#     current_emp = get_employee_by_user(user)
#     if not current_emp:
#         return [user.lower()]

#     allowed_emp_names = {current_emp.name}

#     # Sirf Direct Immediate Subordinates (1 Level Down Only)
#     # Ankit ke liye sirf unke direct reports aayenge (Ekansha, Sparsh, Ritu)
#     # Anurag, Mayur, ya Virendra nahi aayenge kyunki wo Ankit ko report nahi karte.
#     direct_subordinates = frappe.get_all(
#         "Employee",
#         filters={"reports_to": current_emp.name, "status": "Active"},
#         pluck="name"
#     )
#     if direct_subordinates:
#         allowed_emp_names.update(direct_subordinates)

#     # Resolve Employee Names to User IDs (Login Emails)
#     emp_records = frappe.get_all(
#         "Employee",
#         filters={"name": ["in", list(allowed_emp_names)], "status": "Active"},
#         fields=["user_id", "company_email", "prefered_email"]
#     )

#     allowed_users = set()
#     for e in emp_records:
#         u = e.user_id or e.company_email or e.prefered_email
#         if u:
#             allowed_users.add(u.strip().lower())

#     # Current user ko hamesha allow rakhein
#     allowed_users.add(user.strip().lower())

#     return list(allowed_users)


# # ─── Dropdown Link Queries ───────────────────────────────────────────────────

# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_departments(doctype, txt, searchfield, start, page_len, filters):
#     user = frappe.session.user

#     # 1. MD, Founder Office, Admin ko sabhi departments milenge
#     if is_top_management(user):
#         return frappe.db.sql("""
#             SELECT name, department_name FROM `tabDepartment`
#             WHERE name LIKE %(txt)s
#             ORDER BY name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     current_emp = get_employee_by_user(user)
#     if not current_emp:
#         return []

#     # 2. User ka apna department + unke direct subordinates ke departments
#     allowed_departments = set()
#     if current_emp.department:
#         allowed_departments.add(current_emp.department)

#     # Direct subordinates ke departments dhoondein
#     sub_depts = frappe.get_all(
#         "Employee",
#         filters={"reports_to": current_emp.name, "status": "Active"},
#         pluck="department"
#     )
#     for d in sub_depts:
#         if d:
#             allowed_departments.add(d)

#     if not allowed_departments:
#         return []

#     return frappe.db.sql("""
#         SELECT name, department_name FROM `tabDepartment`
#         WHERE name IN %(depts)s 
#           AND (name LIKE %(txt)s OR department_name LIKE %(txt)s)
#         ORDER BY name ASC
#         LIMIT %(start)s, %(page_len)s
#     """, {"depts": tuple(allowed_departments), "txt": f"%{txt}%", "start": start, "page_len": page_len})


# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_assigned_by(doctype, txt, searchfield, start, page_len, filters):
#     user = frappe.session.user
#     if is_top_management(user):
#         return frappe.db.sql("""
#             SELECT name, full_name FROM `tabUser`
#             WHERE enabled = 1 AND user_type = 'System User' AND (name LIKE %(txt)s OR full_name LIKE %(txt)s)
#             ORDER BY name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     # Normal user/manager: Sirf apna User
#     return frappe.db.sql("""
#         SELECT name, full_name FROM `tabUser`
#         WHERE name = %s
#     """, (user,))


# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_allowed_assigned_to(doctype, txt, searchfield, start, page_len, filters):
#     user = frappe.session.user

#     # 1. MD & Founder Office ko pura access
#     if is_top_management(user):
#         return frappe.db.sql("""
#             SELECT u.name, u.full_name
#             FROM `tabUser` u
#             WHERE u.enabled = 1 
#               AND u.user_type = 'System User'
#               AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
#             ORDER BY u.name ASC
#             LIMIT %(start)s, %(page_len)s
#         """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

#     # 2. Strict User Scope (Subordinates + Peers + Self)
#     allowed_users = get_allowed_assignee_users(user)

#     # Edge-case safety: Agar list empty ho jaye toh sirf khud ko return kare
#     if not allowed_users:
#         allowed_users = [user.lower()]

#     # LOWER() match use kar rahe hain taaki email case-sensitivity ka issue na aaye
#     return frappe.db.sql("""
#         SELECT u.name, u.full_name
#         FROM `tabUser` u
#         WHERE LOWER(u.name) IN %(users)s 
#           AND u.enabled = 1
#           AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
#         ORDER BY u.name ASC
#         LIMIT %(start)s, %(page_len)s
#     """, {"users": tuple(allowed_users), "txt": f"%{txt}%", "start": start, "page_len": page_len})


# # ─── APIs for Form Context & Workflows ────────────────────────────────────────

# @frappe.whitelist()
# def get_user_hierarchy_context():
#     user = frappe.session.user
#     top_mgmt = is_top_management(user)

#     if top_mgmt:
#         return {
#             "is_unrestricted": True,
#             "department": None,
#             "current_user": user
#         }

#     emp = get_employee_by_user(user)
#     return {
#         "is_unrestricted": False,
#         "department": emp.department if emp else None,
#         "current_user": user
#     }


# @frappe.whitelist()
# def approve_task(task_name):
#     task = frappe.get_doc("Performance Task", task_name)
#     if task.status != "Pending Approval":
#         frappe.throw(_("Task must be in 'Pending Approval' status to approve."))
#     task.status = "Approved"
#     task.approved_by = frappe.session.user
#     task.approval_status = "Approved"
#     task.save(ignore_permissions=True)
#     task._send_decision_email("Approved")
#     return {"status": "approved", "score": task.score}


# @frappe.whitelist()
# def reject_task(task_name, reason):
#     task = frappe.get_doc("Performance Task", task_name)
#     if task.status != "Pending Approval":
#         frappe.throw(_("Task must be in 'Pending Approval' status to reject."))
#     task.status = "Reopened"
#     task.rejection_reason = reason
#     task.approval_status = "Rejected"
#     task.save(ignore_permissions=True)
#     task._send_decision_email("Rejected", reason)
#     return {"status": "rejected"}


# @frappe.whitelist()
# def get_my_tasks(user=None):
#     user = user or frappe.session.user
#     return frappe.get_all(
#         "Performance Task",
#         filters={"assigned_to": user, "status": ["not in", ["Approved", "Cancelled"]]},
#         fields=["name", "task_title", "status", "priority", "deadline", "is_overdue"],
#         order_by="deadline asc"
#     )


# @frappe.whitelist()
# def generate_tasks_from_template(template_name, assigned_to, deadline):
#     template = frappe.get_doc("Checklist Template", template_name)
#     created = []
#     for item in template.items:
#         task = frappe.get_doc({
#             "doctype": "Performance Task",
#             "task_title": item.item_title,
#             "description": item.description or "",
#             "task_type": template.task_type,
#             "priority": template.default_priority,
#             "department": template.department,
#             "assigned_to": assigned_to,
#             "assigned_by": frappe.session.user,
#             "deadline": deadline,
#             "checklist_template": template_name,
#             "frequency": template.frequency,
#             "status": "Pending"
#         })
#         task.flags.ignore_assignment_email = True
#         task.insert(ignore_permissions=True)
#         created.append(task.name)
#     return {"created": created, "count": len(created)}

# @frappe.whitelist()
# def get_department_by_user(user):
#     """Assigned To user ke basis pe unka exact department fetch karega."""
#     if not user:
#         return None

#     emp = frappe.db.sql("""
#         SELECT department FROM `tabEmployee`
#         WHERE (user_id = %s OR company_email = %s OR prefered_email = %s)
#           AND status = 'Active'
#         LIMIT 1
#     """, (user, user, user), as_dict=True)

#     if emp and emp[0].department:
#         return emp[0].department
#     return None

# def get_permission_query_conditions(user):
#     if not user:
#         user = frappe.session.user
#     if is_top_management(user):
#         return ""
#     return f"(`tabPerformance Task`.assigned_to = '{frappe.db.escape(user)}' OR `tabPerformance Task`.assigned_by = '{frappe.db.escape(user)}')"


# def has_permission(doc, ptype="read", user=None):
#     if not user:
#         user = frappe.session.user
#     if is_top_management(user):
#         return True
#     if doc.assigned_to == user or doc.assigned_by == user:
#         return True
#     return False


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, add_to_date
from performance_management.performance_management.utils.whatsapp import send_dual_notification
from performance_management.performance_management.utils.whatsapp_automation import send_task_critical_score_alert

VALID_STATUSES = ["Draft", "Pending", "In Progress", "Pending Approval", "Approved", "Reopened", "Cancelled"]

# Full Access Roles: Managing Director aur Founder Office poori company me kisi ko bhi assign kar sakte hain
TOP_MANAGEMENT_ROLES = ["Managing Director", "Founder Office", "Administrator", "System Manager"]


class PerformanceTask(Document):

    def validate(self):
        # 1. New task par default score 100
        if self.is_new() and (self.score is None or self.score == 0):
            self.score = 100.0

        # 2. Selected employee ke basis par department auto-sync
        if self.assigned_to:
            dept = get_department_by_user(self.assigned_to)
            if dept:
                self.department = dept

        # 3. Normal managers/users ke liye Assigned By hamesha logged-in user rahega
        if not is_top_management(frappe.session.user) or not self.assigned_by:
            self.assigned_by = frappe.session.user

        # 4. Strict Hierarchy Validation
        self._validate_assigned_to_hierarchy()
        self._set_approval_requirement()
        self._check_overdue()

    def before_save(self):
        # Safe assignment agar field schema me exist kare tabhi set kare
        if self.status == "Pending Approval":
            if hasattr(self, "submission_date") and not self.submission_date:
                self.submission_date = now_datetime()

        self._handle_completion()

    def after_insert(self):
        if not self.flags.ignore_assignment_email:
            self._send_assignment_email()

    def on_update(self):
        if self.has_value_changed("status") and self.status == "Pending Approval":
            self._send_submission_email()
        self._log_audit("Update")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _validate_assigned_to_hierarchy(self):
        user = frappe.session.user
        if not self.assigned_to or is_top_management(user):
            return

        allowed = [u.lower() for u in get_allowed_assignee_users(user)]
        if self.assigned_to.strip().lower() not in allowed:
            frappe.throw(
                _("Aap <b>{0}</b> ko task assign nahi kar sakte. Aap sirf apni direct team ko assign kar sakte hain.")
                .format(self.assigned_to)
            )

    def _set_approval_requirement(self):
        if self.priority in ("High", "Critical") or self.task_type == "Compliance":
            self.requires_approval = 1

    def _check_overdue(self):
        if self.deadline and self.status not in ("Approved", "Cancelled"):
            self.is_overdue = 1 if get_datetime(self.deadline) < now_datetime() else 0

    def _handle_completion(self):
        """When approved, set completion date and calculate score."""
        if self.status == "Approved" and not self.completion_date:
            self.completion_date = now_datetime()
            self._calculate_final_score()

        if self.status == "Reopened":
            if hasattr(self, "submission_date"):
                self.submission_date = None
            self.score = max(0.0, (self.score or 100.0) - 20.0)

    def _calculate_final_score(self):
        base = self.score if self.score is not None else 100.0

        # Safe fallback: submission_date exist kare toh use kare, warna completion_date
        effective_completion = self.get("submission_date") or self.completion_date

        if self.deadline and effective_completion:
            delay = (get_datetime(effective_completion) - get_datetime(self.deadline)).days
            if delay > 0:
                base -= min(delay * 10, 50)

        self.score = max(0.0, base)

    def _log_audit(self, action):
        try:
            frappe.get_doc({
                "doctype": "PM Audit Log",
                "reference_doctype": self.doctype,
                "reference_name": self.name,
                "action": action,
                "user": frappe.session.user,
                "timestamp": now_datetime(),
                "details": f"Status: {self.status} | Priority: {self.priority} | Score: {self.score}"
            }).insert(ignore_permissions=True)
        except Exception:
            pass

    def _send_assignment_email(self):
        if self.assigned_to:
            msg = f"<p>Hello,</p><p>You have been assigned a new task: <strong>{self.task_title}</strong>.</p><p>Priority: <b>{self.priority}</b><br>Deadline: <b>{self.deadline or 'None'}</b></p>"
            wa_msg = f"You have been assigned a new task: *{self.task_title}*.\nPriority: *{self.priority}*\nDeadline: *{self.deadline or 'None'}*"
            send_dual_notification(self.assigned_to, f"New Task Assigned: {self.task_title}", msg, wa_msg)

    def _send_submission_email(self):
        if self.assigned_by:
            msg = f"<p>Hello,</p><p><strong>{self.assigned_to}</strong> has submitted the task <strong>{self.task_title}</strong> for your approval.</p>"
            wa_msg = f"*{self.assigned_to}* has submitted the task *{self.task_title}* for your approval."
            send_dual_notification(self.assigned_by, f"Task Pending Approval: {self.task_title}", msg, wa_msg)

    def _send_decision_email(self, decision, reason=None):
        if self.assigned_to:
            reason_html = f"<p>Manager Comments: {reason}</p>" if reason else ""
            reason_wa = f"\nManager Comments: {reason}" if reason else ""
            color = "green" if decision == "Approved" else "red"
            msg = f"<p>Hello,</p><p>Your task <strong>{self.task_title}</strong> has been <b><span style='color:{color}'>{decision}</span></b>.</p>{reason_html}"
            wa_msg = f"Your task *{self.task_title}* has been *{decision}*.{reason_wa}"
            send_dual_notification(self.assigned_to, f"Task {decision}: {self.task_title}", msg, wa_msg)


# ─── Hierarchy & Role Helpers ────────────────────────────────────────────────

def is_top_management(user):
    """Managing Director, Founder Office aur Administrator/System Manager ko poori company ka access milega."""
    if user == "Administrator":
        return True
    user_roles = frappe.get_roles(user)
    return any(role in user_roles for role in TOP_MANAGEMENT_ROLES)


def get_employee_by_user(user):
    emp = frappe.db.sql("""
        SELECT name, reports_to, department, user_id, employee_name
        FROM `tabEmployee`
        WHERE (user_id = %s OR company_email = %s OR prefered_email = %s)
          AND status = 'Active'
        LIMIT 1
    """, (user, user, user), as_dict=True)
    return emp[0] if emp else None


def get_allowed_assignee_users(user):
    """
    STRICT DOWNWARD ONLY:
    - Normal user/manager sirf apne DIRECT SUBORDINATES (reports_to = current employee)
      aur KHUD (Self) ko hi task assign kar sakega.
    """
    current_emp = get_employee_by_user(user)
    if not current_emp:
        return [user.lower()]

    allowed_emp_names = {current_emp.name}

    direct_subordinates = frappe.get_all(
        "Employee",
        filters={"reports_to": current_emp.name, "status": "Active"},
        pluck="name"
    )
    if direct_subordinates:
        allowed_emp_names.update(direct_subordinates)

    emp_records = frappe.get_all(
        "Employee",
        filters={"name": ["in", list(allowed_emp_names)], "status": "Active"},
        fields=["user_id", "company_email", "prefered_email"]
    )

    allowed_users = set()
    for e in emp_records:
        u = e.user_id or e.company_email or e.prefered_email
        if u:
            allowed_users.add(u.strip().lower())

    allowed_users.add(user.strip().lower())
    return list(allowed_users)


# ─── Auto-Extension & Penalty Engine (Cron Job) ──────────────────────────────

def auto_extend_overdue_tasks():
    """
    Scheduler Job:
    1. Overdue pending tasks ko identify karega.
    2. Deadline ko EXACT 48 Hours (+2 Days) aage badhayega.
    3. extension_count me +1 karega.
    4. Score me se 25 points deduct karega.
    5. Score <= 25 hone par WhatsApp/Email critical warning trigger karega.
    """
    now = now_datetime()
    overdue_tasks = frappe.get_all(
        "Performance Task",
        filters={
            "deadline": ["<", now],
            "status": ["in", ["Draft", "Pending", "In Progress", "Reopened"]]
        },
        fields=["name", "task_title", "deadline", "score", "extension_count", "assigned_to"]
    )

    for task_data in overdue_tasks:
        doc = frappe.get_doc("Performance Task", task_data.name)

        # 1. Exact 48 Hours extension
        current_deadline = get_datetime(doc.deadline)
        doc.deadline = add_to_date(current_deadline, hours=48)

        # 2. Extension count +1 aur Score -25.0
        doc.extension_count = (doc.extension_count or 0) + 1
        current_score = doc.score if doc.score is not None else 100.0
        doc.score = max(0.0, current_score - 25.0)
        doc.is_overdue = 1

        doc.flags.ignore_permissions = True
        doc.flags.ignore_assignment_email = True
        doc.save()

        # 3. Alert jab score 25 ya usse kam ho jaye
        if doc.score <= 25.0 and doc.assigned_to:
            msg = (
                f"<p>Dear Team Member,</p>"
                f"<p>Your task <b>{doc.task_title}</b> (ID: {doc.name}) is overdue.</p>"
                f"<p>25 points have been deducted. Your current score is: <b>{doc.score}</b><br>"
                f"Auto Extension Count: <b>{doc.extension_count}</b><br>"
                f"New Extended Deadline (+48 hrs): <b>{doc.deadline}</b></p>"
            )
            wa_msg = (
                f"⚠️ *Task Alert: Overdue*\n"
                f"Your task *{doc.task_title}* ({doc.name}) is overdue.\n"
                f"25 points deducted! Current Score: *{doc.score}*\n"
                f"Total Extensions: *{doc.extension_count}*\n"
                f"New Extended Deadline (+48 hrs): *{doc.deadline}*"
            )
            send_dual_notification(
                doc.assigned_to,
                f"Warning: Task Overdue ({doc.task_title})",
                msg,
                wa_msg
            )
            try:
                send_task_critical_score_alert(doc)
            except Exception:
                pass


# ─── Dropdown Link Queries ───────────────────────────────────────────────────

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_departments(doctype, txt, searchfield, start, page_len, filters):
    user = frappe.session.user

    if is_top_management(user):
        return frappe.db.sql("""
            SELECT name, department_name FROM `tabDepartment`
            WHERE name LIKE %(txt)s
            ORDER BY name ASC
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    current_emp = get_employee_by_user(user)
    if not current_emp:
        return []

    allowed_departments = set()
    if current_emp.department:
        allowed_departments.add(current_emp.department)

    sub_depts = frappe.get_all(
        "Employee",
        filters={"reports_to": current_emp.name, "status": "Active"},
        pluck="department"
    )
    for d in sub_depts:
        if d:
            allowed_departments.add(d)

    if not allowed_departments:
        return []

    return frappe.db.sql("""
        SELECT name, department_name FROM `tabDepartment`
        WHERE name IN %(depts)s 
          AND (name LIKE %(txt)s OR department_name LIKE %(txt)s)
        ORDER BY name ASC
        LIMIT %(start)s, %(page_len)s
    """, {"depts": tuple(allowed_departments), "txt": f"%{txt}%", "start": start, "page_len": page_len})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_assigned_by(doctype, txt, searchfield, start, page_len, filters):
    user = frappe.session.user
    if is_top_management(user):
        return frappe.db.sql("""
            SELECT name, full_name FROM `tabUser`
            WHERE enabled = 1 AND user_type = 'System User' AND (name LIKE %(txt)s OR full_name LIKE %(txt)s)
            ORDER BY name ASC
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    return frappe.db.sql("""
        SELECT name, full_name FROM `tabUser`
        WHERE name = %s
    """, (user,))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_assigned_to(doctype, txt, searchfield, start, page_len, filters):
    user = frappe.session.user

    if is_top_management(user):
        return frappe.db.sql("""
            SELECT u.name, u.full_name
            FROM `tabUser` u
            WHERE u.enabled = 1 
              AND u.user_type = 'System User'
              AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
            ORDER BY u.name ASC
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    allowed_users = get_allowed_assignee_users(user)
    if not allowed_users:
        allowed_users = [user.lower()]

    return frappe.db.sql("""
        SELECT u.name, u.full_name
        FROM `tabUser` u
        WHERE LOWER(u.name) IN %(users)s 
          AND u.enabled = 1
          AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
        ORDER BY u.name ASC
        LIMIT %(start)s, %(page_len)s
    """, {"users": tuple(allowed_users), "txt": f"%{txt}%", "start": start, "page_len": page_len})


# ─── APIs for Form Context & Workflows ────────────────────────────────────────

@frappe.whitelist()
def get_user_hierarchy_context():
    user = frappe.session.user
    top_mgmt = is_top_management(user)

    if top_mgmt:
        return {
            "is_unrestricted": True,
            "department": None,
            "current_user": user
        }

    emp = get_employee_by_user(user)
    return {
        "is_unrestricted": False,
        "department": emp.department if emp else None,
        "current_user": user
    }


@frappe.whitelist()
def approve_task(task_name):
    task = frappe.get_doc("Performance Task", task_name)
    if task.status != "Pending Approval":
        frappe.throw(_("Task must be in 'Pending Approval' status to approve."))
    task.status = "Approved"
    task.approved_by = frappe.session.user
    task.approval_status = "Approved"
    task.save(ignore_permissions=True)
    task._send_decision_email("Approved")
    return {"status": "approved", "score": task.score}


@frappe.whitelist()
def reject_task(task_name, reason):
    task = frappe.get_doc("Performance Task", task_name)
    if task.status != "Pending Approval":
        frappe.throw(_("Task must be in 'Pending Approval' status to reject."))
    task.status = "Reopened"
    task.rejection_reason = reason
    task.approval_status = "Rejected"
    task.save(ignore_permissions=True)
    task._send_decision_email("Rejected", reason)
    return {"status": "rejected"}


@frappe.whitelist()
def get_my_tasks(user=None):
    user = user or frappe.session.user
    return frappe.get_all(
        "Performance Task",
        filters={"assigned_to": user, "status": ["not in", ["Approved", "Cancelled"]]},
        fields=["name", "task_title", "status", "priority", "deadline", "is_overdue"],
        order_by="deadline asc"
    )


@frappe.whitelist()
def generate_tasks_from_template(template_name, assigned_to, deadline):
    template = frappe.get_doc("Checklist Template", template_name)
    created = []
    for item in template.items:
        task = frappe.get_doc({
            "doctype": "Performance Task",
            "task_title": item.item_title,
            "description": item.description or "",
            "task_type": template.task_type,
            "priority": template.default_priority,
            "department": template.department,
            "assigned_to": assigned_to,
            "assigned_by": frappe.session.user,
            "deadline": deadline,
            "checklist_template": template_name,
            "frequency": template.frequency,
            "status": "Pending",
            "score": 100.0,
            "extension_count": 0
        })
        task.flags.ignore_assignment_email = True
        task.insert(ignore_permissions=True)
        created.append(task.name)
    return {"created": created, "count": len(created)}


@frappe.whitelist()
def get_department_by_user(user):
    if not user:
        return None

    emp = frappe.db.sql("""
        SELECT department FROM `tabEmployee`
        WHERE (user_id = %s OR company_email = %s OR prefered_email = %s)
          AND status = 'Active'
        LIMIT 1
    """, (user, user, user), as_dict=True)

    if emp and emp[0].department:
        return emp[0].department
    return None


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    if is_top_management(user):
        return ""
    return f"(`tabPerformance Task`.assigned_to = '{frappe.db.escape(user)}' OR `tabPerformance Task`.assigned_by = '{frappe.db.escape(user)}')"


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user
    if is_top_management(user):
        return True
    if doc.assigned_to == user or doc.assigned_by == user:
        return True
    return False