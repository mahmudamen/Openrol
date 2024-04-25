from odoo import models, fields

class SchoolResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    is_school_calendar = fields.Boolean(string="Is School Calendar")
