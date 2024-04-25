# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    group_school_batch_setting = fields.Boolean("Active Batches", implied_group='de_school.group_school_batch_setting')
