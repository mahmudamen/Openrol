# -*- coding: utf-8 -*-

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, exceptions, fields, models, _


class Course(models.Model):
    _inherit = 'oe.school.course'

    company_currency = fields.Many2one("res.currency", string='Currency', compute="_compute_company_currency", readonly=True)
    is_application_revenue = fields.Boolean(string='Allow Expected Revenue', compute='_compute_admission_setting_values')
    expected_revenue = fields.Monetary('Expected Fee', currency_field='company_currency')
    
    def _compute_admission_setting_values(self):
        application_revenue = self.env['ir.config_parameter'].sudo().get_param('de_school_admission.is_application_revenue', False)
        for record in self:
            record.is_application_revenue = application_revenue

    @api.depends('company_id')
    def _compute_company_currency(self):
        for lead in self:
            if not lead.company_id:
                lead.company_currency = self.env.company.currency_id
            else:
                lead.company_currency = lead.company_id.currency_id
