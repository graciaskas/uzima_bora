from odoo import models


class AttendanceXls(models.AbstractModel):
    _name='report.attendance.xls'
    _inherit="report.report_xlsx.abstract"