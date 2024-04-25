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
    _order = 'start_datetime,id desc'
    _rec_name = 'name'
    _check_company_auto = True
    
    name = fields.Text('Note', compute='_compute_name', store=True)
    course_id = fields.Many2one('oe.school.course', 'Course', store=True, required=True)
    batch_id = fields.Many2one('oe.school.course.batch', 'Batch', store=True, required=True)
    subject_id = fields.Many2one('oe.school.course.subject', 'Subject', store=True, required=True)
    teacher_id = fields.Many2one('hr.employee', 'Teacher', store=True, domain="[('is_teacher','=',True)]")
    user_id = fields.Many2one('res.users',compute='_compute_user_from_teacher', store=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    calendar_id = fields.Many2one('resource.calendar', related='company_id.resource_calendar_id')
    
    classroom_id = fields.Many2one('oe.school.building.room', 'Classroom', store=True,)
    
    start_datetime = fields.Datetime("Start Date", compute='_compute_datetime', store=True, readonly=False, required=True, copy=True)
    end_datetime = fields.Datetime("End Date", compute='_compute_datetime', store=True, readonly=False, required=True, copy=True)
    color = fields.Integer("Color", compute='_compute_color' )
    allocated_hours = fields.Float("Allocated Hours", compute='_compute_allocated_hours', store=True, readonly=False)
    allocated_percentage = fields.Float("Allocated Time (%)", default=100,
        compute='_compute_allocated_percentage', store=True, readonly=False,
        help="Percentage of time the employee is supposed to work during the shift.",
        group_operator="avg")
    
    state = fields.Selection([
            ('draft', 'Draft'),
            ('published', 'Published'),
    ], string='Status', default='draft')
    is_hatched = fields.Boolean(compute='_compute_is_hatched')
    timetable_period_id = fields.Many2one('resource.calendar.attendance', string='Period Templates', readonly=False, store=True, domain="[('calendar_id','=',calendar_id)]")
    
    # Recurring (`repeat_` fields are none stored, only used for UI purpose)
    recurrency_id = fields.Many2one('oe.school.timetable.recurrency', readonly=True, index=True, ondelete="set null", copy=False)
    repeat = fields.Boolean("Repeat", compute='_compute_repeat', inverse='_inverse_repeat')
    repeat_interval = fields.Integer("Repeat every", default=1, compute='_compute_repeat_interval', inverse='_inverse_repeat')
    repeat_type = fields.Selection([('forever', 'Forever'), ('until', 'Until')], string='Repeat Type', default='forever', compute='_compute_repeat_type', inverse='_inverse_repeat')
    repeat_until = fields.Date("Repeat Until", compute='_compute_repeat_until', inverse='_inverse_repeat', help="If set, the recurrence stop at that date. Otherwise, the recurrence is applied indefinitely.")
    
    
    @api.constrains('timetable_period_id', 'start_datetime')
    def _check_timetable_period(self):
        for record in self:
            timetables = self.filtered(lambda tt: tt.timetable_period_id and tt.start_datetime)
        if not timetables:
            return

        self.env["oe.school.timetable"].flush([
            "start_datetime", "timetable_period_id",
        ])
        
        # /!\ Computed stored fields are not yet inside the database.
        self._cr.execute('''
            SELECT tt2.id
            FROM oe_school_timetable tt
            JOIN oe_school_timetable_period period ON period.id = tt.timetable_period_id
            INNER JOIN oe_school_timetable tt2 ON
                tt2.start_datetime = tt.start_datetime
                AND tt2.timetable_period_id = period.id
                AND tt2.id != tt.id
            WHERE tt.id IN %s
        ''', [tuple(timetables.ids)])
        duplicated_tts = self.browse([r[0] for r in self._cr.fetchall()])
        if duplicated_tts:
            raise ValidationError(_('Duplicated period detected. You probably encoded twice the same period:\n%s') % "\n".join(
                duplicated_tts.mapped(lambda m: "%(date_start)s" % {
                    'date_start': m.start_datetime,
                })
            ))
            
    def _get_tz(self):
        return (self.env.user.tz
                or self._context.get('tz')
                or self.company_id.resource_calendar_id.tz
                or 'UTC')
    
    @api.depends('timetable_period_id')
    def _compute_datetime(self):
        for tt in self.filtered(lambda s: s.timetable_period_id):
            tt.start_datetime, tt.end_datetime = self._calculate_start_end_dates(tt.start_datetime,
                                                                                     tt.end_datetime,
                                                                                     tt.timetable_period_id,
                                                                                     )
    
    @api.model
    def _calculate_start_end_dates(self,
                                 start_datetime,
                                 end_datetime,
                                 timetable_period_id,
                                 ):

        def convert_datetime_timezone(dt, tz):
            return dt and pytz.utc.localize(dt).astimezone(tz)

        user_tz = pytz.timezone(self._get_tz())

        h = int(timetable_period_id.hour_from)
        m = round(modf(timetable_period_id.hour_from)[0] * 60.0)
        start = pytz.utc.localize(start_datetime).astimezone(pytz.timezone(tt.company_id.resource_calendar_id.tz))
        start = start.replace(hour=int(h), minute=int(m))
        start = start.astimezone(pytz.utc).replace(tzinfo=None)
            
        h2 = int(timetable_period_id.hour_to)
        m2 = round(modf(timetable_period_id.hour_to)[0] * 60.0)
        end = pytz.utc.localize(start_datetime).astimezone(pytz.timezone(tt.company_id.resource_calendar_id.tz))
        end = end.replace(hour=int(h2), minute=int(m2))
        end = end.astimezone(pytz.utc).replace(tzinfo=None)
            
        return (start, end)

    @api.depends('course_id','batch_id','subject_id','company_id')
    def _compute_name(self):
        for record in self:
            record.name = record.course_id.code + '/' + record.batch_id.name + ' - ' + record.subject_id.code
            
    @api.depends('course_id.color', 'subject_id.color')
    def _compute_color(self):
        for tt in self:
            tt.color = tt.subject_id.color or tt.course_id.color
            
    @api.depends('teacher_id')
    def _compute_user_from_teacher(self):
        for tt in self:
            tt.user_id = tt.teacher_id.user_id.id
            
    @api.depends('start_datetime', 'end_datetime', 'allocated_hours')
    def _compute_allocated_percentage(self):
        for tt in self:
            tt.allocated_percentage = 100
            
    @api.depends('state')
    def _compute_is_hatched(self):
        for tt in self:
            tt.is_hatched = tt.state == 'draft'



    # Reapeat periods functionality
    @api.depends('recurrency_id')
    def _compute_repeat(self):
        for tt in self:
            if tt.recurrency_id:
                tt.repeat = True
            else:
                tt.repeat = False

    @api.depends('recurrency_id.repeat_interval')
    def _compute_repeat_interval(self):
        for tt in self:
            if tt.recurrency_id:
                tt.repeat_interval = slot.recurrency_id.repeat_interval
            else:
                tt.repeat_interval = False

    @api.depends('recurrency_id.repeat_until')
    def _compute_repeat_until(self):
        for tt in self:
            if tt.recurrency_id:
                tt.repeat_until = tt.recurrency_id.repeat_until
            else:
                tt.repeat_until = False

    @api.depends('recurrency_id.repeat_type')
    def _compute_repeat_type(self):
        for tt in self:
            if tt.recurrency_id:
                tt.repeat_type = slot.recurrency_id.repeat_type
            else:
                tt.repeat_type = False

    def _inverse_repeat(self):
        for tt in self:
            if tt.repeat and not tt.recurrency_id.id:  # create the recurrence
                repeat_until = False
                if tt.repeat_type == "until":
                    repeat_until = datetime.combine(fields.Date.to_date(tt.repeat_until), datetime.max.time())
                    repeat_until = repeat_until.replace(tzinfo=pytz.timezone(tt.company_id.resource_calendar_id.tz or 'UTC')).astimezone(pytz.utc).replace(tzinfo=None)
                recurrency_values = {
                    'repeat_interval': tt.repeat_interval,
                    'repeat_until': repeat_until,
                    'repeat_type': tt.repeat_type,
                    'company_id': tt.company_id.id,
                }
                recurrence = self.env['oe.school.timetable.recurrency'].create(recurrency_values)
                tt.recurrency_id = recurrence
                tt.recurrency_id._repeat_timetable()
            # user wants to delete the recurrence
            # here we also check that we don't delete by mistake a slot of which the repeat parameters have been changed
            elif not tt.repeat and tt.recurrency_id.id and (
                tt.repeat_type == tt.recurrency_id.repeat_type and
                tt.repeat_until == tt.recurrency_id.repeat_until and
                tt.repeat_interval == tt.recurrency_id.repeat_interval
            ):
                tt.recurrency_id._delete_period(tt.end_datetime)
                tt.recurrency_id.unlink()  # will set recurrency_id to NULL
                
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
