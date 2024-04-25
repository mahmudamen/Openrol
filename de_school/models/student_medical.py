# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class StudentMedicalcat(models.Model):
    _name = 'oe.school.medical.cat'
    _description = 'Medical Category'

    name = fields.Char(string='Name', required=True)

class StudentMedicaltype(models.Model):
    _name = 'oe.school.medical.type'
    _description = 'Medical Types'

    name = fields.Char(string='Name', required=True)
    med_cat_id = fields.Many2one('oe.school.medical.cat', string='Category', required=True)

class StudentMedical(models.Model):
    _name = 'oe.school.student.medical'
    _description = 'Student Medical History'


    student_id = fields.Many2one('res.partner', string='Student', required=True, ondelete='cascade', index=True, copy=False)
    med_cat_id = fields.Many2one('oe.school.medical.cat', string='Category', required=True)
    med_type_id = fields.Many2one('oe.school.medical.type', string='Type', required=True,
                                 domain="[('med_cat_id','=',med_cat_id)]"
                                 )
    med_condition = fields.Text(string='Condition')
    med_remarks = fields.Text(string='Remarks')
    