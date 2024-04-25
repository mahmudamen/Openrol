# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import json
import logging
import pytz
import uuid
from math import ceil, modf

class SchoolTimetable(models.Model):
    _name = 'oe.school.timetable'
    _description = 'School Timetable'
    _order = 'date,id desc'
    _rec_name = 'name'
    _check_company_auto = True

    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week',
                                 compute='_compute_dayofweek', store=True,
                                )
    
    name = fields.Text('Note', compute='_compute_name', store=True)
    course_id = fields.Many2one('oe.school.course', 'Course', store=True, required=True)

    use_batch = fields.Boolean(compute='_compute_batch_from_course')
    batch_id = fields.Many2one('oe.school.course.batch', 'Batch', store=True,)

    use_section = fields.Boolean(compute='_compute_section_from_company')
    section_id = fields.Many2one('oe.school.course.section', 'Section', store=True,)
    
    subject_id = fields.Many2one('oe.school.subject', 'Subject', store=True, required=True)
    teacher_id = fields.Many2one('hr.employee', 'Teacher', 
                                 store=True, 
                                 domain="[('is_teacher','=',True)]"
                                )
    user_id = fields.Many2one('res.users',compute='_compute_user_from_teacher', store=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    
    classroom_id = fields.Many2one('oe.school.building.room', 
                                   'Classroom', 
                                   store=True,
                                  )
    date = fields.Date('Date', required=True)
    hour_from = fields.Float(string='From', required=True)
    hour_to = fields.Float(string='To', required=True)
    duration = fields.Float('Duration', 
                            #compute='_compute_duration', 
                            store=True, readonly=False)
    color = fields.Integer("Color", compute='_compute_color' )
    allday = fields.Boolean('All Day', default=False)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('published', 'Published'),
    ], string='Status', default='draft')
    

    #@api.constrains('course_id', 'batch_id', 'subject_id', 'dayofweek')
    #def _check_duplicate_timetable(self):
    #    for record in self:
    #        domain = [
    #            ('course_id', '=', record.course_id.id),
    #            ('batch_id', '=', record.batch_id.id),
    #            ('subject_id', '=', record.subject_id.id),
    #            ('dayofweek', '=', record.dayofweek),
    #        ]
    #        if self.search_count(domain) > 1:
    #            raise UserError("Timetable already exists.")

    @api.constrains('course_id', 'subject_id', 'teacher_id', 'batch_id', 'section_id', 'hour_from', 'hour_to')
    def _check_duplicate_timetable(self):
        for record in self:
            domain = [
                ('course_id', '=', record.course_id.id),
                ('subject_id', '=', record.subject_id.id),
                ('teacher_id', '=', record.teacher_id.id),
                ('batch_id', '=', record.batch_id.id),
                ('section_id', '=', record.section_id.id),
                ('date','=',record.date),
            ]
            if record.id:
                domain.append(('id', '!=', record.id))
            timetable_ids = self.search(domain).filtered(lambda x:
                    x.hour_from <= record.hour_to
                    and x.hour_to >= record.hour_from
                )
            #raise UserError(len(timetable_ids))           
            if len(timetable_ids) > 0:
                raise UserError("Timesheet already scheduled for the specified date and time.")

    
    def _compute_batch_from_course(self):
        for record in self:
            if record.course_id.use_batch and len(record.course_id.batch_ids) > 0:
                record.use_batch = True
            else:
                record.use_batch = False

    def _compute_section_from_company(self):
        for record in self:
            record.use_section = record.course_id.company_id.use_section

    
    def _get_tz(self):
        return (self.env.user.tz
                or self._context.get('tz')
                or self.company_id.resource_calendar_id.tz
                or 'UTC')

    @api.depends('course_id', 'subject_id', 'date', 'hour_from', 'hour_to')
    def _compute_name(self):
        for record in self:
            course_code = record.course_id.code if record.course_id else ''
            subject_code = record.subject_id.code if record.subject_id else ''
            date_str = record.date.strftime('%A') if record.date else ''
            hour_from_time = self._float_to_time(record.hour_from) if record.hour_from else ''
            hour_to_time = self._float_to_time(record.hour_to) if record.hour_to else ''
    
            # Construct the name using the formatted values
            record.name = f"{course_code}/{subject_code} On {date_str} ({hour_from_time} to {hour_to_time})"

    @api.depends('date')
    def _compute_dayofweek(self):
        for record in self:
            record.dayofweek = str(record.date.weekday())
            
            
    def _float_to_time(self, float_value):
        hour = int(float_value)
        minutes = int((float_value - hour) * 60)
        return time(hour=hour, minute=minutes)

            

            
    @api.depends('course_id.color', 'subject_id.color')
    def _compute_color(self):
        for tt in self:
            tt.color = tt.subject_id.color or tt.course_id.color
            
    @api.depends('teacher_id')
    def _compute_user_from_teacher(self):
        for tt in self:
            tt.user_id = tt.teacher_id.user_id.id
                        
    @api.depends('state')
    def _compute_is_hatched(self):
        for tt in self:
            tt.is_hatched = tt.state == 'draft'


    
                
    # ----------------------------------------------------
    # Business Methods
    # ----------------------------------------------------
    def _add_delta_with_dst(self, start, delta):
        """
        Add to start, adjusting the hours if needed to account for a shift in the local timezone between the
        start date and the resulting date (typically, because of DST)

        :param start: origin date in UTC timezone, but without timezone info (a naive date)
        :return resulting date in the UTC timezone (a naive date)
        """
        try:
            tz = pytz.timezone(self._get_tz())
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC
        start = start.replace(tzinfo=pytz.utc).astimezone(tz).replace(tzinfo=None)
        result = start + delta
        return tz.localize(result).astimezone(pytz.utc).replace(tzinfo=None)

    # -----------------------------------
    # ----------- Actions ---------------
    # -----------------------------------
    def action_timetable_planning(self):
        action = self.env.ref('de_school_timetable.action_timetable_wizard').read()[0]
        action.update({
            'name': 'Timetable Planning',
            'res_model': 'oe.school.timetable.wizard',
            'type': 'ir.actions.act_window',
        })
        return action

    def action_classroom_allocation(self):
        active_ids = self.env.context.get('active_ids')
        timetable_ids = self.env['oe.school.timetable'].search([('id','in',active_ids)])
        if any(tt.date < fields.Date.today() for tt in timetable_ids):
            raise UserError(_("Some of the selected schedules have already expired. Please choose active schedules."))
        return {
            'name': 'Room Allocation',
            'view_mode': 'form',
            'res_model': 'oe.school.tt.room.alloc.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_teacher_assignment(self):
        active_ids = self.env.context.get('active_ids')
        timetable_ids = self.env['oe.school.timetable'].search([('id','in',active_ids)])
        if any(tt.date < fields.Date.today() for tt in timetable_ids):
            raise UserError(_("Some of the selected schedules have already expired. Please choose active schedules."))
        return {
            'name': 'Assign Teacher',
            'view_mode': 'form',
            'res_model': 'oe.school.tt.assign.teacher.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        