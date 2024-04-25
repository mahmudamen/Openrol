# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ExamGrade(models.Model):
    _name = 'oe.exam.grade'
    _description = 'Exam Grading System'
    _order = "name asc"

    name = fields.Char(string='Name', required=True)
    enable_credit_points = fields.Boolean('Enable Credit Points')

    exam_grade_line = fields.One2many('oe.exam.grade.line', 'exam_grade_id', string='Exam Grade Lines')

class ExamGradeLine(models.Model):
    _name = 'oe.exam.grade.line'
    _description = 'Exam Grading Line'

    exam_grade_id = fields.Many2one('oe.exam.grade', string='Exam Grade')
    name = fields.Char(string='Grade', required=True)
    score_min = fields.Float(string='Min Score (%)')
    credit_points = fields.Float(string='Credit Points')
    
    