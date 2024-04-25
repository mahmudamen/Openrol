# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Lead2OpportunityMassConvert(models.TransientModel):
    _name = 'oe.admission.lead2op.wizard'
    _description = 'Convert Enquiry to Application (in mass)'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, index=True, readonly=False)
    user_id = fields.Many2one(
        'res.users', string='Admission Officer', default=lambda self: self.env.user,
        domain="['&', ('share', '=', False), ('company_ids', 'in', company_id)]",
        check_company=True, index=True, tracking=True)
    team_id = fields.Many2one(
        'oe.admission.team', string='Admission Team', check_company=True, index=True, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        compute='_compute_team_id', ondelete="set null", readonly=False, store=True)
    
    # Academic Fields
    admission_register_id = fields.Many2one('oe.admission.register',string="Admission Register", required=True)
    
    course_id = fields.Many2one('oe.school.course', string='Course', compute='_compute_from_admission_register')
    course_code = fields.Char(related='course_id.code')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', domain="[('course_id','=',course_id)]")

    @api.depends('user_id')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for admission in self:
            # setting user as void should not trigger a new team computation
            if not admission.user_id:
                continue
            user = admission.user_id
            if admission.team_id and user in (admission.team_id.member_ids | admission.team_id.user_id):
                continue
            team_domain = [] #[('use_leads', '=', True)] if lead.type == 'lead' else [('use_leads', '=', True)]
            team = self.env['oe.admission.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            admission.team_id = team.id

    @api.depends('admission_register_id')
    def _compute_from_admission_register(self):
        for record in self:
            record.course_id = record.admission_register_id.course_id.id
    
    def action_mass_convert(self):
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        record_ids = self.env[active_model].search([('id','in',active_ids)])
        for record in record_ids:
            record.write({
                'type': 'opportunity',
                'team_id': self.team_id.id,
                'user_id': self.user_id.id,
            })
            if not record.admission_register_id:
                record.write({
                    'admission_register_id': self.admission_register_id.id,
                })
    