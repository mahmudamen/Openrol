# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrderFeesTemplate(models.Model):
    _name = "sale.order.fees.template"
    _description = "Fees Template"

    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign

    def _get_default_require_payment(self):
        return self.env.company.portal_confirmation_pay

    name = fields.Char('Fees Template', required=True)
    sale_order_fees_template_line_ids = fields.One2many('sale.order.fees.template.line', 'sale_order_fees_template_id', 'Lines', copy=True)
    note = fields.Html('Terms and conditions', translate=True)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, help='Request a online signature to the customer in order to confirm orders automatically.')
    require_payment = fields.Boolean('Online Payment', default=_get_default_require_payment, help='Request an online payment to the customer in order to confirm orders automatically.')
    mail_template_id = fields.Many2one(
        'mail.template', 'Confirmation Mail',
        domain=[('model', '=', 'sale.order')],
        help="This e-mail template will be sent on confirmation. Leave empty to send nothing.")
    active = fields.Boolean(default=True, help="If unchecked, it will allow you to hide the quotation template without removing it.")
    company_id = fields.Many2one('res.company', string='Company')

    @api.constrains('company_id', 'sale_order_fees_template_line_ids')
    def _check_company_id(self):
        for template in self:
            companies = template.mapped('sale_order_fees_template_line_ids.product_id.company_id')
            if len(companies) > 1:
                raise ValidationError(_("Your template cannot contain products from multiple companies."))
            elif companies and companies != template.company_id:
                raise ValidationError(_(
                    "Your template contains products from company %(product_company)s whereas your template belongs to company %(template_company)s. \n Please change the company of your template or remove the products from other companies.",
                    product_company=', '.join(companies.mapped('display_name')),
                    template_company=template.company_id.display_name,
                ))

    @api.onchange('sale_order_fees_template_line_ids')
    def _onchange_template_line_ids(self):
        companies = self.mapped('sale_order_fees_template_line_ids.product_id.company_id')
        if companies and self.company_id not in companies:
            self.company_id = companies[0]

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SaleOrderFeesTemplate, self).create(vals_list)
        records._update_product_translations()
        return records

    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            companies = self.env['res.company'].sudo().search([('sale_order_template_id', 'in', self.ids)])
            companies.sale_order_template_id = None
        result = super(SaleOrderFeesTemplate, self).write(vals)
        self._update_product_translations()
        return result

    def _update_product_translations(self):
        languages = self.env['res.lang'].search([('active', '=', 'true')])
        for lang in languages:
            for line in self.sale_order_fees_template_line_ids:
                if line.name == line.product_id.get_product_multiline_description_sale():
                    self.create_or_update_translations(model_name='sale.order.fees.template.line,name', lang_code=lang.code,
                                                       res_id=line.id,src=line.name,
                                                       value=line.product_id.with_context(lang=lang.code).get_product_multiline_description_sale())
                    
    def create_or_update_translations(self, model_name, lang_code, res_id, src, value):
        data = {
            'type': 'model',
            'name': model_name,
            'lang': lang_code,
            'res_id': res_id,
            'src': src,
            'value': value,
            'state': 'inprogress',
        }
        existing_trans = self.env['ir.translation'].search([('name', '=', model_name),
                                                            ('res_id', '=', res_id),
                                                            ('lang', '=', lang_code)])
        if not existing_trans:
            self.env['ir.translation'].create(data)
        else:
            existing_trans.write(data)



class SaleOrderFeesTemplateLine(models.Model):
    _name = "sale.order.fees.template.line"
    _description = "Fees Template Line"
    _order = 'sale_order_fees_template_id, sequence, id'

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of sale quote lines.",
        default=10)
    sale_order_fees_template_id = fields.Many2one(
        'sale.order.fees.template', 'Fees Template Reference',
        required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one('res.company', related='sale_order_fees_template_id.company_id', store=True, index=True)
    name = fields.Text('Description', required=True, translate=True)
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain=[('sale_ok', '=', True)])
    product_uom_qty = fields.Float('Quantity', required=True, digits='Product Unit of Measure', default=1)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.name = self.product_id.get_product_multiline_description_sale()

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(product_id=False, product_uom_qty=0, product_uom_id=False)
        return super(SaleOrderFeesTemplateLine, self).create(values)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return super(SaleOrderFeesTemplateLine, self).write(values)

    _sql_constraints = [
        ('accountable_product_id_required',
            "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND product_uom_id IS NOT NULL))",
            "Missing required product and UoM on accountable sale quote line."),

        ('non_accountable_fields_null',
            "CHECK(display_type IS NULL OR (product_id IS NULL AND product_uom_qty = 0 AND product_uom_id IS NULL))",
            "Forbidden product, unit price, quantity, and UoM on non-accountable sale quote line"),
    ]



