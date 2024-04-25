# -*- coding: utf-8 -*-

import requests
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
class TimetableWizard(models.TransientModel):
    _name = "oe.school.timetable.wizard"
    _description = 'Timetable Wizard'

    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', 
    )
    
    course_id = fields.Many2one('oe.school.course', 'Course', store=True, required=True)
    
    use_batch = fields.Boolean(compute='_compute_batch_from_course')
    batch_id = fields.Many2one('oe.school.course.batch', 'Batch', store=True)
    use_section = fields.Boolean(compute='_compute_section_from_company')
    section_id = fields.Many2one('oe.school.course.section', 'Section',)
    
    subject_id = fields.Many2one('oe.school.subject', 'Subject', store=True, required=True)
    teacher_id = fields.Many2one('hr.employee', 'Teacher', store=True, domain="[('is_teacher','=',True)]")
    user_id = fields.Many2one('res.users',compute='_compute_user_from_teacher', store=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    calendar_id = fields.Many2one('resource.calendar', related='company_id.resource_calendar_id')
    classroom_id = fields.Many2one('oe.school.building.room', 'Classroom', store=True,)
    
    date_start = fields.Date("Start Date", compute='_compute_datetime', store=True, readonly=False)
    date_end = fields.Date("End Date", compute='_compute_datetime', store=True, readonly=False)

    hour_from = fields.Float(string='From', required=True)
    hour_to  = fields.Float(string='To', required=True)

    repeat_interval = fields.Integer("Repeat Every", default=1, )
    repeat_type = fields.Selection(
        [
            ('month', 'Month(s)'),
            ('week', 'Week(s)'),
            ('day', 'Day(s)'),
        ],
        string="Repeat Type", required=True, default='week',
        help="Repeat type determines how often a course timetable schedule."
    )

    def _compute_batch_from_course(self):
        for record in self:
            if record.course_id.use_batch and len(record.course_id.batch_ids) > 0:
                record.use_batch = True
            else:
                record.use_batch = False

    def _compute_section_from_company(self):
        for record in self:
            record.use_section = record.course_id.company_id.use_section
            
    @api.depends('batch_id')
    def _compute_datetime(self):
        for record in self:
            record.date_start = record.batch_id.date_start
            record.date_end = record.batch_id.date_end
            
    def action_create_timetable(self):  
        # Check if dates are null
        if not self.date_start or not self.date_end:
            raise UserError(_("Please specify both start date and end date."))

        # Check if hours are null or invalid
        if not self.hour_from > 0 or not self.hour_to > 0 or self.hour_from >= self.hour_to:
            raise UserError(_("Please specify valid hours."))

        current_date = self.date_start
        end_date = self.date_end

        #raise UserError(current_date.weekday())
        if self.repeat_type != 'day':
            selected_day_index = int(self.dayofweek)
            days_until_selected_day = (selected_day_index - current_date.weekday() + 7) % 7
            current_date += timedelta(days=days_until_selected_day)
        while current_date <= end_date:
            #attendance_records = self._find_school_time(current_date)
            #raise UserError(self._find_school_holiday(current_date, self.hour_from, self.hour_to))
            #raise UserError(current_date.weekday())
        
            if not self._find_timetable(current_date):
                if self._find_school_time(current_date):
                    if not self._find_school_holiday(current_date, self.hour_from, self.hour_to):
                        self._create_timetable_records(current_date)
            else:
                pass
                
            #if attendance_records:
            #    self._create_timetable_records(current_date)

    
            if self.repeat_type == 'day':
                current_date += timedelta(days=self.repeat_interval)
            elif self.repeat_type == 'week':
                current_date += timedelta(weeks=self.repeat_interval)
            elif self.repeat_type == 'month':
                # Adding 1 month to the current date
                year = current_date.year + (current_date.month // 12)
                month = (current_date.month % 12) + self.repeat_interval
                current_date = current_date.replace(year=year, month=month, day=1)
    
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Timetable'),
            'res_model': 'oe.school.timetable',
            'view_id': self.env.ref('de_school_timetable.school_timetable_tree_view').id,  # Replace 'your_module' with your module's name
            #'context': {'create': False, 'edit': False},
        }
        return action

    def _find_school_time(self, current_date):
        attendance_records = self.env['resource.calendar.attendance'].search([
            ('dayofweek', '=', str(current_date.weekday())),
            ('calendar_id','=',self.course_id.company_id.resource_calendar_id.id),
        ])
        filter_attendance_records = attendance_records.filtered(lambda x:
                x.hour_from <= self.hour_to
                and x.hour_to >= self.hour_from
        )
        #raise UserError(filter_attendance_records.mapped('name'))
        return filter_attendance_records

    from datetime import datetime

    def _find_school_holiday(self, current_date, hour_from, hour_to):
        if isinstance(hour_from, float) and isinstance(hour_to, float):
            hour_from_str = str(hour_from).replace('.', ':')  # Convert float to string and format as HH:MM
            hour_to_str = str(hour_to).replace('.', ':')  # Convert float to string and format as HH:MM
            
            datetime_from = datetime.combine(current_date, datetime.strptime(hour_from_str, "%H:%M").time())
            datetime_to = datetime.combine(current_date, datetime.strptime(hour_to_str, "%H:%M").time())
            
            holiday_records = self.env['resource.calendar.leaves'].search([
               ('date_from', '<=', datetime_to),
                ('date_to', '>=', datetime_from),
                ('calendar_id','=',self.course_id.company_id.resource_calendar_id.id),
                ('resource_id','=',False)
            ])
            #raise UserError(holiday_records)
            return bool(holiday_records)
        else:
            return False  # Return False if hour_from and hour_to are not float values\

    def _create_timetable_records(self, current_date):
        """
        Create timetable records for the given day and time range.
        """
        self.env['oe.school.timetable'].create({
            'course_id': self.course_id.id,
            'batch_id': self.batch_id.id,
            'subject_id': self.subject_id.id,
            'teacher_id': self.teacher_id.id,
            'user_id': self.user_id.id,
            'classroom_id': self.classroom_id.id,
            'date': current_date,
            'hour_from': self.hour_from,
            'hour_to': self.hour_to,
            #'dayofweek': current_date.weekday(),
        })

    def _find_timetable(self, current_date):
        domain = [
            ('course_id','=',self.course_id.id),
            ('subject_id','=',self.subject_id.id),
            #('hour_from', '<=', self.hour_to+1),
            #('hour_to','>=', self.hour_from-1),
            ('date','=',current_date),
            ('dayofweek','=',self.dayofweek),
        ]
        if self.batch_id:
            domain += [('batch_id','=',self.batch_id.id)]
        if self.section_id:
            domain += [('section_id','=',self.section_id.id)]

        timetable_ids = self.env['oe.school.timetable'].search(domain)
        filter_timetable_ids = timetable_ids.filtered(lambda x:
            x.hour_from <= self.hour_to
            and x.hour_to >= self.hour_from
        )
        #raise UserError(filter_timetable_ids.mapped('name'))
        return filter_timetable_ids