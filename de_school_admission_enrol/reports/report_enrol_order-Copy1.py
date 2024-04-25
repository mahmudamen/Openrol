# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError

class EnrolReport(models.Model):
    _inherit = 'report.enrol.order'

    admission_register_id = fields.Many2one('oe.admission.register', string='Admission Register', readonly=True)

    def _select_enrol(self):
        select_ = super(EnrolReport, self)._select_enrol()
        select_ += """,
            s.admission_register_id AS admission_register_id"""
        return select_

    def _select_additional_fields(self):
        additional_fields = super(EnrolReport, self)._select_additional_fields()
        additional_fields['admission_register_id'] = 's.admission_register_id'
        return additional_fields

    def _group_by_enrol(self):
        groupby_ = super(EnrolReport, self)._group_by_enrol()
        groupby_ += """,
            s.admission_register_id """
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
