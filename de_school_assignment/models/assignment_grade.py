# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AssignmentGrade(models.Model):
    _name = 'oe.assignment.grade'
    _description = 'Assignment Grading'
    _order = "name asc"

    name = fields.Char(string='Name', required=True)

    assignment_grade_line = fields.One2many('oe.assignment.grade.line', 'assignment_grade_id', string='Assignment Grade Lines')

class AssignmentGradeLine(models.Model):
    _name = 'oe.assignment.grade.line'
    _description = 'Assignment Grading Line'

    assignment_grade_id = fields.Many2one('oe.assignment.grade', string='Assignment Grade')
    name = fields.Char(string='Grade', required=True)
    score_min = fields.Float(string='Min Score (%)')
    
    