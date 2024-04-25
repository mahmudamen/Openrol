# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MarksheetGroup(models.Model):
    _name = 'oe.exam.msheet.group'
    _description = 'Marksheet Group'
    _order = "name asc"

    name = fields.Char(string='Name', required=True)
    ms_group_line = fields.One2many('oe.exam.msheet.group.line', 'ms_group_id', string='Marksheet Group Lines')

    @api.constrains('ms_group_line')
    def _check_grade_weightage_sum(self):
        for group in self:
            total_weightage = sum(group.ms_group_line.mapped('grade_weightage'))
            if total_weightage < 0 or total_weightage > 100:
                raise ValidationError("Total Weightage must be between 0 and 100.")


class MarksheetGroupLine(models.Model):
    _name = 'oe.exam.msheet.group.line'
    _description = 'Marksheet Group Line'

    ms_group_id = fields.Many2one('oe.exam.msheet.group', ondelete='restrict', string='Marksheet Group')
    exam_type_id = fields.Many2one('oe.exam.type', string='Exam Type', required=True)
    grade_weightage = fields.Float(string='Weightage', required=True)

    _sql_constraints = [
        ('unique_ms_group_exam_type', 'unique(ms_group_id, exam_type_id)', 'Please do not include the exam type more than once.'),
    ]
    