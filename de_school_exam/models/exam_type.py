# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Examtype(models.Model):
    _name = 'oe.exam.type'
    _description = 'Exam Type'

    name = fields.Char(string='Name', required=True)