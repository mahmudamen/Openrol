# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    admission_team_id = fields.Many2one(
        'oe.admission.team', string='Admission Team',
        compute='_compute_admission_team_id',
        precompute=True,
        ondelete='set null', readonly=False, store=True)

    @api.depends('parent_id')
    def _compute_admission_team_id(self):
        for partner in self.filtered(lambda partner: not partner.admission_team_id and partner.company_type == 'person' and partner.parent_id.admission_team_id):
            partner.admission_team_id = partner.parent_id.admission_team_id