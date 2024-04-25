# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression


class AdmissionRegister(models.Model):
    _inherit = "oe.admission.register"

    enrol_orders_count = fields.Integer(
        string='# Enrol Orders', compute='_compute_enrol_orders_data')
    enrol_orders_amount = fields.Monetary(
        string='Enrol Orders Revenues', compute='_compute_enrol_orders_data')

    # To Invoice Orders
    enrol_toinvoice_count = fields.Integer(
        string='# Enrol Orders', compute='_compute_enrol_orders_toinvoice_data')
    enrol_toinvoice_amount = fields.Monetary(
        string='Enrol Orders Revenues', compute='_compute_enrol_orders_toinvoice_data')

    
    def _compute_enrol_orders_data(self):
        for record in self:
            order_ids = self.env['sale.order'].search([('admission_register_id','=',record.id),('is_enrol_order','=',True)])
            record.enrol_orders_count = len(order_ids)
            record.enrol_orders_amount = sum(order_ids.mapped('amount_total'))

    def _compute_enrol_orders_toinvoice_data(self):
        for record in self:
            order_ids = self.env['sale.order'].search([('admission_register_id','=',record.id),('is_enrol_order','=',True),('invoice_status','=','to invoice')])
            record.enrol_toinvoice_count = len(order_ids)
            record.enrol_toinvoice_amount = sum(order_ids.mapped('amount_total'))

    
    def action_open_enrol_orders(self):
        action = self.env["ir.actions.actions"]._for_xml_id("de_school_enrollment.enrollment_order_action")
        action['context'] = self._prepare_enrol_order_context()
        action['domain'] = expression.AND([[('is_enrol_order', '=', True)], self._get_enrol_order_domain()])
        return action

    def action_open_pending_fees(self):
        action = self.env["ir.actions.actions"]._for_xml_id("de_school_enrollment.enrollment_order_action")
        action['context'] = self._prepare_enrol_order_context()
        action['domain'] = expression.AND([[('is_enrol_order', '=', True),('invoice_status','=','to invoice')], self._get_enrol_order_domain()])
        return action

    def _get_enrol_order_domain(self):
        return [('admission_register_id', '=', self.id)]
         
    def _prepare_enrol_order_context(self):
        """ Prepares the context for a new quotation (sale.order) by sharing the values of common fields """
        self.ensure_one()
        order_context = {
            'default_admission_register_id': self.id,
            'search_default_admission_register_id': self.id,
            'search_default_inprogress_orders': 1,
            'create':False,
        }
        order_context['default_admission_register_id'] = self.id
        order_context['default_create_uid'] = self.env.user.id
        return order_context