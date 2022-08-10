import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, nowdate
from erpnext.hr.doctype.employee.employee import is_holiday
from erpnext.hr.utils import validate_active_employee, validate_dates
from erpnext.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe.model.workflow import apply_workflow
from one_fm.utils import send_workflow_action_email


class AttendanceRequestOverride(AttendanceRequest):
	def validate(self):
		validate_active_employee(self.employee)
		validate_future_dates(self, self.from_date, self.to_date)
		if self.half_day:
			if not getdate(self.from_date) <= getdate(self.half_day_date) <= getdate(self.to_date):
				frappe.throw(_("Half day date should be in between from date and to date"))

	def on_submit(self):
		self.create_attendance()

	def on_cancel(self):
		self.cancel_requested_attendance()

	def cancel_requested_attendance(self):
		attendance_list = frappe.get_list(
			"Attendance", {"employee": self.employee, "attendance_request": self.name}
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	def on_update(self):
		self.send_notification()

	def on_update_after_submit(self):
		self.send_notification()
		if self.update_request:
			if self.workflow_state == 'Approved':
				self.create_attendance()
			if self.workflow_state == 'Update Request':
				self.cancel_requested_attendance()

	def check_shift_assignment(self, attendance_date):
		"""
			Check if shift exist for employee
		"""
		if(frappe.db.exists("Shift Assignment",
			{'employee':self.employee, 'docstatus':1, 'status':'Active', 'start_date':attendance_date})):
			shift_assignment = frappe.db.get_list("Shift Assignment",
				{'employee':self.employee, 'docstatus':1, 'status':'Active', 'start_date':attendance_date})
			return frappe.get_doc("Shift Assignment", shift_assignment[0].name)
		return False

	def check_attendance(self, attendance_date):
		"""check if attendance exist"""
		attendance = frappe.db.exists("Attendance",
			{'employee':self.employee, 'docstatus':1, 'attendance_date':attendance_date}
		)
		if attendance:
			return frappe.get_doc("Attendance", attendance)
		return False

	def create_attendance(self):
		if(not self.future_request):
			request_days = date_diff(self.to_date, self.from_date) + 1
			for number in range(request_days):
				attendance_date = add_days(self.from_date, number)
				skip_attendance = self.validate_if_attendance_not_applicable(attendance_date)
				if not skip_attendance:
					self.mark_attendance(attendance_date)

	def create_future_attendance(self):
		reports_to = self.reports_to()
		if not reports_to:
			frappe.throw("You are not the employee supervisor")
		if(self.future_request and (getdate(self.from_date) <= getdate(nowdate()) <= getdate(self.to_date))):
			attendance_date = nowdate()
			skip_attendance = self.validate_if_attendance_not_applicable(attendance_date)
			if not skip_attendance:
				self.mark_attendance(attendance_date)


	def mark_attendance(self, attendance_date):
		try:
			check_shift_assignment = self.check_shift_assignment(attendance_date)
			if check_shift_assignment:
				check_attendance = self.check_attendance(attendance_date)

				if check_attendance:
					if check_attendance.status=='Absent':
						check_attendance.db_set('Status', 'Work From Home')
						check_attendance.db_set('attendance_request', self.name)
						check_attendance.reload()
				else:
					attendance = frappe.new_doc("Attendance")
					attendance.employee = self.employee
					attendance.employee_name = self.employee_name
					if self.half_day and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0:
						attendance.status = "Half Day"
					elif self.reason == "Work From Home":
						attendance.status = "Work From Home"
					else:
						attendance.status = "Present"
					attendance.attendance_date = attendance_date
					attendance.company = self.company
					attendance.attendance_request = self.name
					attendance.operations_shift = check_shift_assignment.shift
					attendance.roster_type = check_shift_assignment.roster_type
					attendance.shift = check_shift_assignment.shift_type
					attendance.project = check_shift_assignment.project
					attendance.site = check_shift_assignment.site
					attendance.post_type = check_shift_assignment.post_type
					attendance.save(ignore_permissions=True)
					attendance.submit()
		except Exception as e:
			frappe.log_error(str(e), 'Attendance Request')


	def send_notification(self):
		if self.workflow_state in ['Pending Approval', 'Rejected', 'Approved', 'Update Request', 'Cancelled']:
			send_workflow_action_email(self, [self.get_reports_to()])


	def validate_if_attendance_not_applicable(self, attendance_date):
		# Check if attendance_date is a Holiday
		if is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date), alert=1
			)
			return True

		# Check if employee on Leave
		leave_record = frappe.db.sql(
			"""select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""",
			(self.employee, attendance_date),
			as_dict=True,
		)
		if leave_record:
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, self.employee),
				alert=1,
			)
			return True

		return False

	def get_reports_to(self):
		return frappe.db.get_value("Employee", {'name':frappe.db.get_value("Employee", {'name':self.employee}, ['reports_to'])}, ['user_id'])

	@frappe.whitelist()
	def reports_to(self):
		reports_to = self.get_reports_to()
		if (self.employee == 'HR-EMP-00001' and (frappe.session.user in ['abdullah@one-fm.com', 'e.anthony@armor-services.com'])):
			return True
		if not frappe.session.user in [reports_to, 'administrator', 'Administrator', 'abdullah@one-fm.com']:
			frappe.msgprint('This Attendance Request can only be approved by the employee supervisor')
			return False
		return True


def validate_future_dates(doc, from_date, to_date):
	date_of_joining, relieving_date = frappe.db.get_value(
		"Employee", doc.employee, ["date_of_joining", "relieving_date"]
	)
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("To date can not be less than from date"))
	elif (getdate(from_date) > getdate(nowdate()) or (getdate(to_date) > getdate(nowdate()))) and (not doc.future_request):
		frappe.throw(_("Future dates not allowed"))
	elif ((getdate(from_date) < getdate(nowdate())) or (getdate(from_date) < getdate(nowdate()))) and (doc.future_request):
		frappe.throw(_("Past dates not allowed for future request"))
	elif date_of_joining and getdate(from_date) < getdate(date_of_joining):
		frappe.throw(_("From date can not be less than employee's joining date"))
	elif relieving_date and getdate(to_date) > getdate(relieving_date):
		frappe.throw(_("To date can not greater than employee's relieving date"))



@frappe.whitelist()
def update_request(attendance_request, from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	attendance_request_obj = frappe.get_doc('Attendance Request', attendance_request)
	validate_future_dates(attendance_request_obj, from_date, to_date)
	attendance_request_obj.db_set("from_date", from_date)
	attendance_request_obj.db_set("to_date", to_date)
	attendance_request_obj.db_set("update_request", True)
	apply_workflow(attendance_request_obj, "Update Request")
