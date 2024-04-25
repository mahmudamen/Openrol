# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    admission_id = fields.Many2one(
        'oe.admission', string='Application', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    admission_register_id = fields.Many2one('oe.admission.register',string="Admission Register")

    
    def action_confirm(self):
        return super(SaleOrder, self.with_context({k:v for k,v in self._context.items() if k != 'default_tag_ids'})).action_confirm()

    @api.onchange('admission_id')
    def _onchange_admission_id(self):
        self.admission_register_id = self.admission_id.admission_register_id.id
        self.admission_team_id = self.admission_id.team_id.id
