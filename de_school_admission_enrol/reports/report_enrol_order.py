# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class EnrolReport(models.Model):
    _name = "report.enrol.order"
    _inherit = "report.enrol.order"

    admission_register_id = fields.Many2one('oe.admission.register', string='Admission Register', readonly=True)
    

    def _with_enrol(self):
        return ""

    def _select_enrol(self):
        select_ = f"""
            MIN(l.id) AS id,
            l.product_id AS product_id,
            t.uom_id AS product_uom,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS product_uom_qty,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_delivered / u.factor * u2.factor) ELSE 0 END AS qty_delivered,
            CASE WHEN l.product_id IS NOT NULL THEN SUM((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) ELSE 0 END AS qty_to_deliver,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END AS qty_invoiced,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END AS qty_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_total
                / {self._case_value_or_one('s.currency_rate')}
                * {self._case_value_or_one('currency_table.rate')}
                ) ELSE 0
            END AS price_total,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_subtotal
                / {self._case_value_or_one('s.currency_rate')}
                * {self._case_value_or_one('currency_table.rate')}
                ) ELSE 0
            END AS price_subtotal,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_to_invoice
                / {self._case_value_or_one('s.currency_rate')}
                * {self._case_value_or_one('currency_table.rate')}
                ) ELSE 0
            END AS untaxed_amount_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_invoiced
                / {self._case_value_or_one('s.currency_rate')}
                * {self._case_value_or_one('currency_table.rate')}
                ) ELSE 0
            END AS untaxed_amount_invoiced,
            COUNT(*) AS nbr,
            s.name AS name,
            s.date_order AS date,
            s.state AS state,
            s.enrol_status AS enrol_status,
            s.partner_id AS partner_id,
            s.user_id AS user_id,
            s.company_id AS company_id,
            s.campaign_id AS campaign_id,
            s.medium_id AS medium_id,
            s.source_id AS source_id,
            t.categ_id AS categ_id,
            s.pricelist_id AS pricelist_id,
            s.analytic_account_id AS analytic_account_id,
            s.admission_team_id AS admission_team_id,
            s.admission_register_id AS admission_register_id,
            s.is_enrol_order,
            p.product_tmpl_id,
            partner.country_id AS country_id,
            partner.industry_id AS industry_id,
            partner.commercial_partner_id AS commercial_partner_id,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS weight,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS volume,
            l.discount AS discount,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_unit * l.product_uom_qty * l.discount / 100.0
                / {self._case_value_or_one('s.currency_rate')}
                * {self._case_value_or_one('currency_table.rate')}
                ) ELSE 0
            END AS discount_amount,
            s.id AS order_id"""

        additional_fields_info = self._select_additional_fields()
        template = """,
            %s AS %s"""
        for fname, query_info in additional_fields_info.items():
            select_ += template % (query_info, fname)

        return select_

    def _case_value_or_one(self, value):
        return f"""CASE COALESCE({value}, 0) WHEN 0 THEN 1.0 ELSE {value} END"""

    def _select_additional_fields(self):
        """Hook to return additional fields SQL specification for select part of the table query.

        :returns: mapping field -> SQL computation of field, will be converted to '_ AS _field' in the final table definition
        :rtype: dict
        """
        return {}

    def _from_enrol(self):
        return """
            sale_order_line l
            LEFT JOIN sale_order s ON s.id=l.order_id
            JOIN res_partner partner ON s.partner_id = partner.id
            LEFT JOIN product_product p ON l.product_id=p.id
            LEFT JOIN product_template t ON p.product_tmpl_id=t.id
            LEFT JOIN uom_uom u ON u.id=l.product_uom
            LEFT JOIN uom_uom u2 ON u2.id=t.uom_id
            JOIN {currency_table} ON currency_table.company_id = s.company_id
            """.format(
            currency_table=self.env['res.currency']._get_query_currency_table(
                {
                    'multi_company': True,
                    'date': {'date_to': fields.Date.today()}
                }),
            )

    def _where_enrol(self):
        return """
            l.display_type IS NULL and t.fee_product=True """

    def _group_by_enrol(self):
        groupby_ = """
            l.product_id,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.enrol_status,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.admission_team_id,
            s.admission_register_id,
            s.is_enrol_order,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,
            s.id,
            currency_table.rate"""
        return groupby_

    def _query(self):
        with_ = self._with_enrol()
        return f"""
            {"WITH" + with_ + "(" if with_ else ""}
            SELECT {self._select_enrol()}
            FROM {self._from_enrol()}
            WHERE {self._where_enrol()}
            GROUP BY {self._group_by_enrol()}
            {")" if with_ else ""}
        """

    @property
    def _table_query(self):
        return self._query()
