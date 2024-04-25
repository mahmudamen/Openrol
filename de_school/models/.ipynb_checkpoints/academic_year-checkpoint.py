from odoo import models, fields, api
from datetime import timedelta


class SchoolAcademicYear(models.Model):
    _name = 'oe.school.year'
    _description = 'oe.academic.year'
 
    name = fields.Char('Name',required=True)
    date_start = fields.Date('Date Start', required = True)
    date_end = fields.Date('Date end',required = True)
    active = fields.Boolean('Active')