# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    #group_school_batch_setting = fields.Boolean("Active Batches", implied_group='de_school.group_school_batch_setting')
    is_school = fields.Boolean(related='company_id.is_school', readonly=False)
    school_type = fields.Selection(related='company_id.school_type', readonly=False)
    resource_calendar_id = fields.Many2one(related='company_id.resource_calendar_id', readonly=False)
    use_batch = fields.Boolean(related='company_id.use_batch', readonly=False)
    use_section = fields.Boolean(related='company_id.use_section', readonly=False)

    #@api.onchange('school_type')
    #def _change_school_type(self):
    #    for record in self:
    #        if record.school_type in ('col','uni'):
    #            record.use_batch = True
    #        else:
    #            record.use_batch = False
