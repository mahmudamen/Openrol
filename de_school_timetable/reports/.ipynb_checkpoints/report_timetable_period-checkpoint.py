# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReprotTimetable_period(models.Model):
    _name = "oe.report.timetable.period"
    _description = "Period Report"
    _auto = False
    
    name = fields.Char('Name', readonly=True)
    dayofweek = fields.Char('Day Of Week', readonly=True)
    day_period = fields.Char('Day Period', readonly=True)
    calendar_id = fields.Many2one('resource.calendar', string='Calendar', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    
    hour_from = fields.Float(string='Period From', readonly=True)
    hour_to = fields.Float(string='Period To', readonly=True)
    
    def _pr(self):
        pr_str = """
        select ca.id, ca.name, ca.dayofweek, ca.hour_from, ca.hour_to, ca.day_period, ca.calendar_id, c.id as company_id
from resource_calendar_attendance ca
join res_company c on c.resource_calendar_id = ca.calendar_id
where c.is_school = True
        """
        return pr_str

    def _from(self):
        return """(%s)""" % (self._pr())

    def _get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT id AS id,
                name,
                dayofweek,
                day_period,
                calendar_id,
                company_id,
                hour_from,
                hour_to
                
                FROM %s
                AS foo""" % (self._table, self._from())
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self._get_main_request())

        
    