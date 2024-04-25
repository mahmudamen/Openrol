# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def default_get(self, fields):
        if self.env.context.get('default_admission_id'):
            self = self.with_context(
                default_res_model_id=self.env.ref('crm.model_crm_lead').id,
                default_res_id=self.env.context['default_admission_id']
            )
        defaults = super(CalendarEvent, self).default_get(fields)

        # sync res_model / res_id to admission id (aka creating meeting from lead chatter)
        if 'admission_id' not in defaults:
            if self._is_application(defaults, self.env.context):
                defaults['admission_id'] = defaults.get('res_id', False) or self.env.context.get('default_res_id', False)

        return defaults

    admission_id = fields.Many2one(
        'oe.admission', 'Application', domain="[('type', '=', 'opportunity')]",
        index=True, ondelete='set null')

    def _compute_is_highlighted(self):
        super(CalendarEvent, self)._compute_is_highlighted()
        if self.env.context.get('active_model') == 'oe.admission':
            admission_id = self.env.context.get('active_id')
            for event in self:
                if event.admission_id.id == admission_id:
                    event.is_highlighted = True

    @api.model_create_multi
    def create(self, vals):
        events = super(CalendarEvent, self).create(vals)
        for event in events:
            if event.admission_id and not event.activity_ids:
                event.admission_id.log_meeting(event.name, event.start, event.duration)
        return events

    def _is_application(self, defaults, ctx=None):
        """
            This method checks if the concerned model is a CRM lead.
            The information is not always in the defaults values,
            this is why it is necessary to check the context too.
        """
        res_model = defaults.get('res_model', False) or ctx and ctx.get('default_res_model')
        res_model_id = defaults.get('res_model_id', False) or ctx and ctx.get('default_res_model_id')

        return res_model and res_model == 'oe.admission' or res_model_id and self.env['ir.model'].sudo().browse(res_model_id).model == 'oe.admission'
