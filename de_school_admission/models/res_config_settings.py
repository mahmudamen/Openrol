# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, exceptions, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_use_enquiries = fields.Boolean(string="Leads", implied_group='de_school_admission.group_use_enquiries')
    is_application_score = fields.Boolean(string='Application Score', config_parameter='de_school_admission.is_application_score')
    is_application_revenue = fields.Boolean(string='Application Expected Revenue', config_parameter='de_school_admission.is_application_revenue')