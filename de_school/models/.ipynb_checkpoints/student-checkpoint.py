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
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch')
    subject_ids = fields.Many2many('oe.school.course.subject', string='Subjects', compute='_compute_subjects')
    
    enrollment_ids = fields.One2many('oe.school.student.enrollment', 'partner_id', 'Enrollments')
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
    
    # Medical Info
    student_complexion = fields.Char('Complexion') 
    student_weight = fields.Float('Weight (in kg)') 
    student_height = fields.Float('Height (in cm)')
    student_mark_identify = fields.Text('Mark for Identity')
    student_clinic_history = fields.Text('Clinical History')
    student_allergic_history = fields.Text('Allergic History')
    student_emergency_contact = fields.Char('Emergency Contact Name') 
    student_emergency_phone = fields.Char('Emergency Contact Number')
    
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
        subject_ids = self.env['oe.school.course.subject'].search(['|',('course_ids','in',self.course_id.id),('batch_ids','in',self.batch_id.id)])
        self.subject_ids = subject_ids.ids
    
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
            
class StudentEnrollment(models.Model):
    _name = 'oe.school.student.enrollment'
    _description = 'Student Enrollment'
    
    partner_id = fields.Many2one('res.partner', string='Student', required=True, ondelete='cascade', index=True, copy=False)
    school_name = fields.Char('School Name')
    school_year = fields.Char('School Year')
    level_grade = fields.Char('Grading Level')
    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    address_school = fields.Char('School Address')

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
    

    
    