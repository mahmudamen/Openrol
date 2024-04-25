# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, time
from odoo.osv import expression


class AssignmentType(models.Model):
    _name = 'oe.assignment.type'
    _description = 'Assignment Type'

    name = fields.Char(string='Name', required=True)

