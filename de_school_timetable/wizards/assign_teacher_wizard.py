# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError

class AssignTeacher(models.TransientModel):
    _name = 'oe.school.tt.assign.teacher.wizard'
    _description = 'Assign Teacher Wizard'
 
    timetable_ids = fields.Many2many(
        'oe.school.timetable', default=lambda self: self.env.context.get('active_ids'))
    
    teacher_id = fields.Many2one('hr.employee', string='Teacher', 
                                 domain="[('is_teacher','=',True)]",
                                  store=True, readonly=False, required=True
                                 )

    def action_assign_teacher(self):
        for tt in self.timetable_ids:
            tt.write({
                'teacher_id': self.teacher_id.id,
            })