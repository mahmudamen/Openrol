# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.tools.mail import is_html_empty


class AdmissionConfirmWizard(models.TransientModel):
    _name = 'oe.admission.confirm.wizard'
    _description = 'Confirm Admission'

    admission_ids = fields.Many2many(
        'oe.admission', default=lambda self: self.env.context.get('active_ids'))

    course_id = fields.Many2one('oe.school.course', string='Course',
                                default=lambda self: self.env.context.get('course_id'),
                                readonly=True,
                               )
    use_batch = fields.Boolean(default=lambda self: self.env.context.get('use_batch'))
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(default=lambda self: self.env.context.get('use_section'))
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                               domain="[('course_id','=',course_id)]"
                              )

    def action_confirm_admission(self):
        for admission in self.admission_ids:
            #self._convert_handle_student(admission)
            self._confirm_admission(admission)
            admission._handle_student_assignment(force_partner_id=False, create_missing=True)
            self._update_enrollment_history(admission)

    def _confirm_admission(self, admission):
        admission.write({
            'admission_confirmed':True,
            'batch_id': self.batch_id.id,
            'section_id': self.section_id.id,
        })

    def _update_enrollment_history(self, admission):
        enrollment_ids = self.env['oe.school.student.enrollment'].search([
            ('model','=','oe.admission'),('res_id','=',admission.id)
        ])
        for enrollment in enrollment_ids:
            enrollment.write({
                'model': 'res.partner',
                'res_id': admission.partner_id.id,
            })
        
    def _convert_handle_student(self, admission_id):
        student_id = admission_id._find_matching_partner(email_only=True).id
        #return super(AdmissionConfirmWizard, self)._convert_handle_student(admission_id)
