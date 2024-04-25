# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import get_timedelta
from odoo.exceptions import ValidationError


class TimetableRecurrency(models.Model):
    _name = 'oe.school.timetable.recurrency'
    _description = "Timetable Recurrence"
    
    timetable_ids = fields.One2many('oe.school.timetable', 'recurrency_id', string="Related Timetable Entries")
    repeat_interval = fields.Integer("Repeat Every", default=1, required=True)
    repeat_type = fields.Selection([('forever', 'Forever'), ('until', 'Until')], string='Weeks', default='forever')
    repeat_until = fields.Datetime(string="Repeat Until", help="Up to which date should the plannings be repeated")
    last_generated_end_datetime = fields.Datetime("Last Generated End Date", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True, required=True, default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('check_repeat_interval_positive', 'CHECK(repeat_interval >= 1)', 'Recurrency repeat interval should be at least 1'),
        ('check_until_limit', "CHECK((repeat_type = 'until' AND repeat_until IS NOT NULL) OR (repeat_type != 'until'))", 'A recurrence repeating itself until a certain date must have its limit set'),
    ]

    @api.constrains('company_id', 'timetable_ids')
    def _check_multi_company(self):
        for recurrency in self:
            if any(recurrency.company_id != timetable.company_id for timetable in recurrency.timetable_ids):
                raise ValidationError(_('An timetable must be in the same company as its recurrency.'))
                
    
    def name_get(self):
        result = []
        for recurrency in self:
            if recurrency.repeat_type == 'forever':
                name = _('Forever, every %s week(s)') % (recurrency.repeat_interval,)
            else:
                name = _('Every %s week(s) until %s') % (recurrency.repeat_interval, recurrency.repeat_until)
            result.append([recurrency.id, name])
        return result

    @api.model
    def _cron_schedule_next(self):
        companies = self.env['res.company'].search([])
        now = fields.Datetime.now()
        stop_datetime = None
        for company in companies:
            delta = get_timedelta(company.planning_generation_interval, 'month')

            recurrencies = self.search([
                '&',
                '&',
                ('company_id', '=', company.id),
                ('last_generated_end_datetime', '<', now + delta),
                '|',
                ('repeat_until', '=', False),
                ('repeat_until', '>', now - delta),
            ])
            recurrencies._repeat_timetable(now + delta)

    def _repeat_timetable(self, stop_datetime=False):
        Timetable = self.env['oe.school.timetable']
        for recurrency in self:
            timetab = Timetable.search([('recurrency_id', '=', recurrency.id)], limit=1, order='start_datetime DESC')

            if timetab:
                # find the end of the recurrence
                recurrence_end_dt = False
                if recurrency.repeat_type == 'until':
                    recurrence_end_dt = recurrency.repeat_until

                # find end of generation period (either the end of recurrence (if this one ends before the cron period), or the given `stop_datetime` (usually the cron period))
                #if not stop_datetime:
                #    stop_datetime = fields.Datetime.now() + get_timedelta(recurrency.company_id.planning_generation_interval, 'month')
                range_limit = min([dt for dt in [recurrence_end_dt, stop_datetime] if dt])

                # generate recurring periods
                recurrency_delta = get_timedelta(recurrency.repeat_interval, 'week')
                next_start = Timetable._add_delta_with_dst(timetab.start_datetime, recurrency_delta)

                timetab_values_list = []
                while next_start < range_limit:
                    timetab_values = timetab.copy_data({
                        'start_datetime': next_start,
                        'end_datetime': next_start + (timetab.end_datetime - timetab.start_datetime),
                        'recurrency_id': recurrency.id,
                        'company_id': recurrency.company_id.id,
                        'repeat': True,
                        #'is_published': False
                    })[0]
                    timetab_values_list.append(timetab_values)
                    next_start = Timetable._add_delta_with_dst(next_start, recurrency_delta)

                if timetab_values_list:
                    Timetable.create(timetab_values_list)
                    recurrency.write({'last_generated_end_datetime': timetab_values_list[-1]['start_datetime']})

            else:
                recurrency.unlink()

                
    def _delete_period(self, start_datetime):
        tts = self.env['oe.school.timetable'].search([
            ('recurrency_id', 'in', self.ids),
            ('start_datetime', '>=', start_datetime),
        ])
        tts.unlink()
