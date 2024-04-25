# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.osv import expression


class Admission(models.Model):
    _inherit = 'oe.admission'

    sale_amount_total = fields.Monetary(compute='_compute_sale_data', string="Sum of Orders", help="Untaxed Total of Confirmed Orders", currency_field='company_currency')
    sale_order_count = fields.Integer(compute='_compute_sale_data', string="Number of Enrol Orders")
    order_ids = fields.One2many('sale.order', 'admission_id', string='Orders')

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            company_currency = lead.company_currency or self.env.company.currency_id
            sale_orders = lead.order_ids.filtered_domain(self._get_enrol_order_domain())
            lead.sale_amount_total = sum(
                order.currency_id._convert(
                    order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today()
                )
                for order in sale_orders
            )
            lead.sale_order_count = len(sale_orders)

    def _get_enrol_order_domain(self):
       return [('state', 'not in', ['cancel'])]

    def action_new_enrol_order(self):
        return {
            'name': _('New Contacts'),
            'res_model': 'oe.admission.enrol.student.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'oe.admission',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _action_create_enrol_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("de_school_admission_enrol.action_enrol_order_new")
        action['context'] = self._prepare_enrol_order_context()
        action['context']['search_default_admission_id'] = self.id
        action['context']['active_test'] = True
        return action

    def _prepare_enrol_order_context(self):
        """ Prepares the context for a new quotation (sale.order) by sharing the values of common fields """
        self.ensure_one()
        quotation_context = {
            'default_admission_id': self.id,
            'default_admission_register_id': self.admission_register_id.id,
            'default_course_id': self.course_id.id,
            'default_batch_id': self.batch_id.id,
            'default_partner_id': self.partner_id.id,
            'default_origin': self.name,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],
            'default_is_enrol_order': True,
        }
        if self.team_id:
            quotation_context['default_team_id'] = self.team_id.id
        if self.user_id:
            quotation_context['default_user_id'] = self.user_id.id
        return quotation_context

    def action_view_enrol_order(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("de_school_enrollment.enrollment_order_action")
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_admission_id': self.id,
            'default_is_enrol_order': True,
        }
        action['domain'] = expression.AND([[('admission_id', '=', self.id)], self._get_enrol_order_domain()])
        orders = self.order_ids.filtered_domain(self._get_enrol_order_domain())
        if len(orders) == 1:
            action['views'] = [(self.env.ref('de_school_enrollment.enrol_contract_primary_form_view').id, 'form')]
            action['res_id'] = orders.id
        return action

    def _prepare_student_values(self, partner_name, is_company=False, parent_id=False):
        # Call the original method to get the base result
        res = super(Admission, self)._prepare_student_values(partner_name, is_company, parent_id)

        # Add 'admission_team_id' to the result
        res['admission_team_id'] = self.team_id.id  # Replace 'team_id' with the correct field

        return res

