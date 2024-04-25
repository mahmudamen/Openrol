# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging

from psycopg2 import sql, DatabaseError

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['display_name', 'email', 'ref', 'vat', 'company_registry', 'roll_no','admission_no']  # TODO vat must be sanitized the same way for storing/searching
 
    is_student = fields.Boolean('Is Student')
    is_parent_student = fields.Boolean('Is Parent Student', store=True, compute='_compute_parent')
    contact_type = fields.Selection([
        ('parent', 'Parent'),
        ('address', 'Address'),
    ], string='Contact Type', default='parent')
    relation = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('grand-father', 'Grand Father'),
        ('grand-mother', 'Grand Mother'),
        ('other', 'Other'),
    ], string='Relation')
    is_guardian = fields.Boolean('Is Guardian')
    
    
    # Academic Fields
    roll_no = fields.Char('Roll No')
    admission_no = fields.Char('Admission No')
    
    course_id = fields.Many2one('oe.school.course', string='Course')
    
    use_batch = fields.Boolean(related='course_id.use_batch_subject')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(related='course_id.use_section')
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                                 domain="[('course_id','=',course_id)]"
                              )
    
    student_subject_line = fields.One2many('res.partner.subjects.line', 'student_id', 'Subjects')
    
    enrollment_count = fields.Integer(string='Enrollments', compute='_compute_enrollment_count')

    med_info_ids = fields.One2many('oe.school.student.medical', 'student_id', 'Medical Info')
    med_info_count = fields.Integer(string='Enrollments', compute='_compute_med_info_count')
    
    sibling_ids = fields.One2many('oe.student.sibling', 'partner_id', 'Siblings')
    #student_subject_ids = fields.One2many('oe.school.student.subject', 'partner_id', 'Subjects')
    
    # Demographic Info
    date_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    merital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
        ('divorced', 'Divorced'),
        ('other', 'Other'),
    ], string='Merital Status')
    country_birth = fields.Many2one('res.country','Country of Birth')
    country_nationality = fields.Many2one('res.country','Nationality')

    #Gaurdian 
    guardian_id = fields.Many2one('res.partner', string='Gaurdian', readonly=True, store=True,
                compute='_compute_guardian',
                help='A guardian is a person responsible for the student.',
                                 )
    guardian_name = fields.Char(string='Gaurdian Name', readonly=True, 
                compute='_compute_guardian',
                help='A guardian is a person responsible for the student.',
                                 ) 
    # Medical Info
    student_complexion = fields.Char('Complexion') 
    student_weight = fields.Float('Weight (in kg)') 
    student_height = fields.Float('Height (in cm)')
    student_mark_identify = fields.Text('Mark for Identity')
    student_emergency_contact = fields.Char('Emergency Contact Name') 
    student_emergency_phone = fields.Char('Emergency Contact Number')

    @api.depends('child_ids', 'child_ids.is_guardian')
    def _compute_guardian(self):
        for record in self:
            guardian = record.child_ids.filtered(lambda x: x.is_guardian)
            if guardian:
                record.guardian_id = guardian[0].id
                record.guardian_name = guardian[0].name
            else:
                record.guardian_id = False
                record.guardian_name = False

        
    def _compute_enrollment_count(self):
        enrollment_ids = self.env['oe.school.student.enrollment']
        for record in self:
            record.enrollment_count = len(enrollment_ids.search([('model','=',self._name),('res_id','=',record.id)]))

    def _compute_med_info_count(self):
        for record in self:
            record.med_info_count = len(record.med_info_ids)
            
    @api.onchange('contact_type')
    def _onchange_contact_type(self):
        for record in self:
            if record.contact_type == 'parent':
                record.type = 'contact'
            else:
                record.type = 'other'
    
    @api.depends('parent_id')
    def _compute_parent(self):
        for record in self:
            if record.parent_id.is_student:
                record.is_parent_student = True
            else:
                record.is_parent_student = False
                

    def _compute_subjects(self):
        #subject_ids = self.env['oe.school.course.subject'].search(['|',('course_ids','in',self.course_id.id),('batch_ids','in',self.batch_id.id)])
        self.subject_ids = False #subject_ids.ids

    def _compute_use_batch_from_course(self):
        for record in self:
            if record.course_id.use_batch and len(record.course_id.batch_ids) > 0:
                record.use_batch = True
            else:
                record.use_batch = False
    
            
    def attach_document(self, **kwargs):
        pass
    
    # Generatel Roll Number Method
    def generate_roll_number(self):
        students = self.env['res.partner'].browse(self.env.context.get('active_ids'))
        for student in students:
            if not student.roll_no:
                number = student.course_id.sequence_id.next_by_id()
                student.write({
                    'roll_no': number,
                })

    # -------- Actions ---------------
    def open_enrollment_history(self):
        enrollment_ids = self.env['oe.school.student.enrollment'].search([('model','=',self._name),('res_id','=',self.id)])
        action = self.env.ref('de_school.action_enrollment_history').read()[0]
        action.update({
            'name': 'Enrollment History',
            'view_mode': 'tree',
            'res_model': 'oe.school.student.enrollment',
            'type': 'ir.actions.act_window',
            'domain': [('id','in',enrollment_ids.ids)],
            'context': {
                'default_model': self._name,
                'default_res_id': self.id,
            },
        })
        return action

    def open_medical_info(self):
        action = self.env.ref('de_school.action_medical_history').read()[0]
        action.update({
            'name': 'Medical History',
            'view_mode': 'tree',
            'res_model': 'oe.school.student.medical',
            'type': 'ir.actions.act_window',
            'domain': [('student_id','=',self.id)],
            'context': {
                'default_student_id': self.id,
            },
        })
        return action

class StudentSiblings(models.Model):
    _name = 'oe.student.sibling'
    _description = 'Student Sibling'
    
    name = fields.Many2one('res.partner', 'Student Name', domain="[('is_student','=',True),('is_parent_student','=',False)]", required=True)
    partner_id = fields.Many2one('res.partner', string='Student', required=True, ondelete='cascade', index=True, copy=False)
    course_id = fields.Many2one('oe.school.course', string='Course')
    roll_no = fields.Char(string='Roll Number')
    date_birth = fields.Date('Date of Birth')
    relation = fields.Selection([
        ('brother', 'Brother'),
        ('sister', 'Sister'),
    ], string='Gender', default='brother', required=True)

class SubjectLine(models.Model):
    _name = 'res.partner.subjects.line'
    _description = 'Student Sibling'

    student_id = fields.Many2one('res.partner', 
                                  string='Student', 
                                  required=True, 
                                  ondelete='cascade', 
                                  index=True, copy=False
                                )
    subject_id = fields.Many2one('oe.school.subject', string='Subject', 
                                 required=True,
                                 domain="[('id','in',subject_ids)]"
                                )
    subject_ids = fields.Many2many(
        comodel_name='oe.school.subject',
        string='Courses for Subject',
        compute='_compute_subjects_from_course',
    )
    

    _sql_constraints = [
        ('unique_student_subject', 'UNIQUE(student_id, subject_id)', 'Subject must be unique!'),
    ]

    @api.depends('student_id.course_id')
    def _compute_subjects_from_course(self):
        for record in self:
            if record.student_id.course_id:
                subject_ids = self.env['oe.school.course.subject.line'].search([
                    ('course_id','=',record.student_id.course_id.id)
                ]).mapped('subject_id')
                record.subject_ids = subject_ids
            else:
                record.subject_ids = False    
    
    