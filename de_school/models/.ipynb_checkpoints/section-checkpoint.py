# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SchoolSection(models.Model):
    _name = 'oe.school.course.section'
    _description = 'Curse Section'
    
    name = fields.Char(string='Course', required=True, index=True, translate=True) 
