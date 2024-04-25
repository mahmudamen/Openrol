# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pytz
import threading
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from psycopg2 import sql
from odoo.addons.phone_validation.tools import phone_validation

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.addons.iap.tools import iap_tools
from odoo.addons.mail.tools import mail_validation
#from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import date_utils, email_re, email_split, is_html_empty


_logger = logging.getLogger(__name__)

# Subset of partner fields: sync any of those
PARTNER_FIELDS_TO_SYNC = [
    'lang',
    'mobile',
    'title',
    'function',
    'website',
]

# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'street2',
    'city',
    'zip',
    'state_id',
    'country_id',
]
class Admission(models.Model):
    _name = "oe.admission"
    _description = 'Admission'
    _inherit = [
        'mail.thread.cc',
        'mail.thread.blacklist',
        'mail.thread.phone',
        'mail.activity.mixin',
        'utm.mixin',
        'format.address.mixin',
        'avatar.mixin'
    ]
    _primary_email = 'email_from'
    _check_company_auto = True
    _track_duration_field = 'stage_id'
    
    # Description
    name = fields.Char(string='Reference', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    user_id = fields.Many2one(
        'res.users', string='Admission Officer', default=lambda self: self.env.user,
        domain="['&', ('share', '=', False), ('company_ids', 'in', user_company_ids)]",
        check_company=True, index=True, tracking=True)
    user_company_ids = fields.Many2many(
        'res.company', compute='_compute_user_company_ids',
        help='UX: Limit to lead company or all if no company')
    user_email = fields.Char('User Email', related='user_id.email', readonly=True)
    user_login = fields.Char('User Login', related='user_id.login', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, compute='_compute_company_id', readonly=False, store=True)
    team_id = fields.Many2one(
        'oe.admission.team', string='Admission Team', check_company=True, index=True, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        compute='_compute_team_id', ondelete="set null", readonly=False, store=True)

    referred = fields.Char('Referred By')
    description = fields.Html('Notes')
    active = fields.Boolean('Active', default=True, tracking=True)
    type = fields.Selection([
        ('lead', 'Lead'), ('opportunity', 'Opportunity')],
        index=True, required=True, tracking=15,
        default=lambda self: 'lead' if self.env['res.users'].has_group('de_school_team.group_school_admission_user') else 'opportunity')
    
    # Pipeline management
    stage_id = fields.Many2one(
        'oe.admission.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    kanban_state = fields.Selection([
        ('grey', 'No next activity planned'),
        ('red', 'Next activity late'),
        ('green', 'Next activity is planned')], string='Kanban State',
        compute='_compute_kanban_state')
    tag_ids = fields.Many2many(
        'oe.admission.tag', 'admission_admission_tag_rel', 'lead_id', 'tag_id', string='Tags',
        help="Classify and analyze your lead/opportunity categories like: Training, Service")
    color = fields.Integer('Color Index', default=0)
    
    # Customer / contact
    partner_id = fields.Many2one(
        'res.partner', string='Customer', check_company=True, index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    partner_is_blacklisted = fields.Boolean('Partner is blacklisted', related='partner_id.is_blacklisted', readonly=True)
    contact_name = fields.Char('Contact Name', tracking=30,compute='_compute_contact_name', copy=False, readonly=False, store=True)
    partner_name = fields.Char(
        'Company Name', tracking=20, index=True,
        compute='_compute_partner_name', readonly=False, store=True,copy=False,
        help='The name of the future partner company that will be created while converting the lead into opportunity')
    title = fields.Many2one('res.partner.title', string='Title', compute='_compute_title', readonly=False, store=True)
    email_from = fields.Char(
        'Email', tracking=40, index=True,copy=False,
        compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)
    phone = fields.Char(
        'Phone', tracking=50,
        compute='_compute_phone', inverse='_inverse_phone', copy=False,readonly=False, store=True)
    mobile = fields.Char('Mobile', compute='_compute_mobile', copy=False, readonly=False, store=True)
    phone_state = fields.Selection([
        ('correct', 'Correct'),
        ('incorrect', 'Incorrect')], string='Phone Quality', compute="_compute_phone_state", store=True)
    email_state = fields.Selection([
        ('correct', 'Correct'),
        ('incorrect', 'Incorrect')], string='Email Quality', compute="_compute_email_state", store=True)
    website = fields.Char('Website', index=True, help="Website of the contact", compute="_compute_website", readonly=False, store=True)
    lang_id = fields.Many2one(
        'res.lang', string='Language',
        compute='_compute_lang_id', readonly=False, store=True)
    
    # Address fields
    street = fields.Char('Street', compute='_compute_partner_address_values', readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_partner_address_values', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, compute='_compute_partner_address_values', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_partner_address_values', readonly=False, store=True)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_partner_address_values', readonly=False, store=True)
    
    company_currency = fields.Many2one("res.currency", string='Currency', compute="_compute_company_currency", readonly=True)

    # UX
    partner_email_update = fields.Boolean('Partner Email will Update', compute='_compute_partner_email_update')
    partner_phone_update = fields.Boolean('Partner Phone will Update', ) #compute='_compute_partner_phone_update')
    
    #priority = fields.Selection(string='Priority', index=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority',)

    date_conversion = fields.Datetime('Conversion Date', readonly=True)
    date_deadline = fields.Date('Expected Closing', help="Estimate of the date on which the opportunity will be won.")
    date_closed = fields.Datetime('Closed Date', readonly=True, copy=False)

    
    # Accept and Reject
    won_status = fields.Selection([
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('pending', 'Pending'),
    ], string='Is Won', compute='_compute_won_status', store=True)
    lost_reason_id = fields.Many2one(
        'oe.admission.lost.reason', string='Lost Reason',
        index=True, ondelete='restrict', tracking=True)

    # Academic Fields
    admission_register_id = fields.Many2one('oe.admission.register',string="Admission Register")
    
    course_id = fields.Many2one('oe.school.course', string='Course', compute='_compute_from_admission_register')
    course_code = fields.Char(related='course_id.code')

    use_batch = fields.Boolean(related='course_id.use_batch_subject')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(related='course_id.use_section')
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                                 domain="[('course_id','=',course_id)]"
                              )
    admission_confirmed = fields.Boolean('Admission Confirmed',help='Once the application is converted into a student profile, admission is confirmed.')

    # Probability (Opportunity only)
    is_application_score = fields.Boolean(string='Allow Score', compute='_compute_admission_setting_values')
    is_application_revenue = fields.Boolean(string='Allow Expected Revenue', compute='_compute_admission_setting_values')
    probability = fields.Float(
        'Probability', group_operator="avg", copy=False,
        compute='_compute_probabilities', readonly=False, store=True)
    expected_revenue = fields.Monetary('Expected Revenue', default=0, store=True,
                                       compute='_compute_default_expected_revenue',
                                       currency_field='company_currency', tracking=True)
    prorated_revenue = fields.Monetary('Prorated Revenue', currency_field='company_currency', store=True, compute="_compute_prorated_revenue")

    calendar_event_count = fields.Integer('# Meetings', compute='_compute_calendar_event_count')

    enrollment_count = fields.Integer(string='Enrollments', compute='_compute_enrollment_count')

    # ------------------------------------------------------
    # ----------------- Computed Methods -------------------
    # ------------------------------------------------------

    def _compute_calendar_event_count(self):
        meeting_ids = self.env['calendar.event'].search([('admission_id','=',self.id)])
        for lead in self:
            lead.calendar_event_count = len(meeting_ids)
            
    def _compute_admission_setting_values(self):
        application_score = self.env['ir.config_parameter'].sudo().get_param('de_school_admission.is_application_score', False)
        application_revenue = self.env['ir.config_parameter'].sudo().get_param('de_school_admission.is_application_revenue', False)

        for record in self:
            record.is_application_score = application_score
            record.is_application_revenue = application_revenue
    
    @api.depends('active', 'probability','stage_id')
    def _compute_won_status(self):
        for lead in self:
            if lead.active and lead.probability == 100:
                lead.won_status = 'won'
            elif not lead.active and lead.probability == 0:
                lead.won_status = 'lost'
            else:
                if lead.stage_id.is_close:
                    lead.won_status = 'won'
                else:
                    lead.won_status = 'pending'

    @api.depends('course_id')
    def _compute_default_expected_revenue(self):
         for record in self:
            record.expected_revenue = record.course_id.expected_revenue
        
    @api.onchange('course_id')
    def _onchange_course_id(self):
        for record in self:
            record.expected_revenue = record.course_id.expected_revenue
        
    #@api.depends(lambda self: ['stage_id', 'team_id'] + self._pls_get_safe_fields())
    @api.depends('stage_id', 'admission_register_id', 
                 'admission_register_id.score_ids', 'admission_register_id.score_ids.score')
    def _compute_probabilities(self):
        for admission in self:
            if admission.stage_id:
                # Filter the score_ids related to the admission register that are below the current stage
                stage_scores = admission.admission_register_id.score_ids.filtered(
                    lambda line: line.stage_id.sequence <= admission.stage_id.sequence
                )
                
                # Calculate the total score as the sum of stage scores
                total_score = sum(stage_scores.mapped('score'))
                # Calculate the probability based on the total score
                admission.probability = (total_score / 100) * 100
            else:
                admission.probability = 0


    def _compute_enrollment_count(self):
        enrollment_ids = self.env['oe.school.student.enrollment'].search([
            ('model','=',self._name),
            ('res_id','=',self.id)
        ])
        partner_enrollment_ids = self.env['oe.school.student.enrollment'].search([
            ('model','=','res.partner'),
            ('res_id','=',self.partner_id.id)
        ])
        for record in self:
            record.enrollment_count = len(enrollment_ids.mapped('res_id') + partner_enrollment_ids.mapped('res_id'))
                    
    @api.depends('expected_revenue', 'probability')
    def _compute_prorated_revenue(self):
        for lead in self:
            lead.prorated_revenue = round((lead.expected_revenue or 0.0) * (lead.probability or 0) / 100.0, 2)

    def _pls_get_safe_fields(self):
        """ As config_parameters does not accept M2M field,
            we the fields from the formated string stored into the Char config field.
            To avoid sql injections when using that list, we return only the fields
            that are defined on the model. """
        pls_fields_config = self.env['ir.config_parameter'].sudo().get_param('crm.pls_fields')
        pls_fields = pls_fields_config.split(',') if pls_fields_config else []
        pls_safe_fields = [field for field in pls_fields if field in self._fields.keys()]
        return pls_safe_fields

    @api.depends('partner_id','partner_id.mobile')
    def _compute_mobile(self):
        """ compute the new values when partner_id has changed """
        for admission in self:
            if not admission.mobile or admission.partner_id.mobile:
                admission.mobile = admission.partner_id.mobile

    @api.depends('partner_id',
                 'partner_id.street',
                 'partner_id.street2',
                'partner_id.city',
                 'partner_id.country_id',
                 'partner_id.zip',
                )
    def _compute_partner_address_values(self):
        """ Sync all or none of address fields """
        for admission in self:
            admission.update(admission._prepare_address_values_from_partner(admission.partner_id))

    @api.depends('partner_id',
                 'street',
                 'street2',
                 'city',
                 'country_id',
                 'zip',
                )
    def _update_partner_address_values(self):
        """ Sync all or none of address fields """
        for admission in self:
            raise UserError('hello')
            admission.update(admission.partner_id._prepare_address_values_from_partner(admission.partner_id))
            
    @api.depends('admission_register_id')
    def _compute_from_admission_register(self):
        for record in self:
            record.course_id = record.admission_register_id.course_id.id

    @api.depends('company_id')
    def _compute_user_company_ids(self):
        all_companies = self.env['res.company'].search([])
        for admission in self:
            if not admission.company_id:
                admission.user_company_ids = all_companies
            else:
                admission.user_company_ids = admission.company_id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
        
    @api.depends('team_id', 'type')
    def _compute_stage_id(self):
        for lead in self:
            if not lead.stage_id:
                lead.stage_id = lead._stage_find(domain=[('fold', '=', False)]).id
    
    def _stage_find(self, team_id=False, domain=None, order='sequence, id', limit=1):
        """ Determine the stage of the current lead with its teams, the given domain and the given team_id
            :param team_id
            :param domain : base search domain for stage
            :param order : base search order for stage
            :param limit : base search limit for stage
            :returns oe.admission.stage recordset
        """
        # collect all team_ids by adding given one, and the ones related to the current leads
        team_ids = set()
        if team_id:
            team_ids.add(team_id)
        for lead in self:
            if lead.team_id:
                team_ids.add(lead.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['oe.admission.stage'].search(search_domain, order=order, limit=limit)

    @api.depends('user_id', 'type')
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
    
    @api.depends('user_id', 'team_id', 'partner_id')
    def _compute_company_id(self):
        """ Compute company_id coherency. """
        for lead in self:
            proposal = lead.company_id

            # invalidate wrong configuration
            if proposal:
                # company not in responsible companies
                if lead.user_id and proposal not in lead.user_id.company_ids:
                    proposal = False
                # inconsistent
                if lead.team_id.company_id and proposal != lead.team_id.company_id:
                    proposal = False
                # void company on team and no assignee
                if lead.team_id and not lead.team_id.company_id and not lead.user_id:
                    proposal = False
                # no user and no team -> void company and let assignment do its job
                # unless customer has a company
                if not lead.team_id and not lead.user_id and \
                   (not lead.partner_id or lead.partner_id.company_id != proposal):
                    proposal = False

            # propose a new company based on team > user (respecting context) > partner
            if not proposal:
                if lead.team_id.company_id:
                    proposal = lead.team_id.company_id
                elif lead.user_id:
                    if self.env.company in lead.user_id.company_ids:
                        proposal = self.env.company
                    else:
                        proposal = lead.user_id.company_id & self.env.companies
                elif lead.partner_id:
                    proposal = lead.partner_id.company_id
                else:
                    proposal = False

            # set a new company
            if lead.company_id != proposal:
                lead.company_id = proposal
    
    @api.depends('activity_date_deadline')
    def _compute_kanban_state(self):
        today = date.today()
        for lead in self:
            kanban_state = 'grey'
            if lead.activity_date_deadline:
                lead_date = fields.Date.from_string(lead.activity_date_deadline)
                if lead_date >= today:
                    kanban_state = 'green'
                else:
                    kanban_state = 'red'
            lead.kanban_state = kanban_state
    
    @api.depends('partner_id')
    def _compute_contact_name(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            lead.update(lead._prepare_contact_name_from_partner(lead.partner_id))
            
    @api.depends('partner_id')
    def _compute_partner_name(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            lead.update(lead._prepare_partner_name_from_partner(lead.partner_id))
    
    @api.depends('partner_id')
    def _compute_title(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            if not lead.title or lead.partner_id.title:
                lead.title = lead.partner_id.title
    
    @api.depends('partner_id.email')
    def _compute_email_from(self):
        for lead in self:
            if lead.partner_id.email and lead._get_partner_email_update():
                lead.email_from = lead.partner_id.email

    def _inverse_email_from(self):
        for lead in self:
            if lead._get_partner_email_update():
                lead.partner_id.email = lead.email_from

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        for lead in self:
            if lead.partner_id.phone and lead._get_partner_phone_update():
                lead.phone = lead.partner_id.phone

    def _inverse_phone(self):
        for lead in self:
            if lead._get_partner_phone_update():
                lead.partner_id.phone = lead.phone

    @api.depends('phone', 'country_id.code')
    def _compute_phone_state(self):
        for lead in self:
            phone_status = False
            if lead.phone:
                country_code = lead.country_id.code if lead.country_id and lead.country_id.code else None
                try:
                    if phone_validation.phone_parse(lead.phone, country_code):  # otherwise library not installed
                        phone_status = 'correct'
                except UserError:
                    phone_status = 'incorrect'
            lead.phone_state = phone_status

    @api.depends('email_from')
    def _compute_email_state(self):
        for lead in self:
            email_state = False
            if lead.email_from:
                email_state = 'incorrect'
                for email in email_split(lead.email_from):
                    if mail_validation.mail_validate(email):
                        email_state = 'correct'
                        break
            lead.email_state = email_state

    
    def _prepare_address_values_from_partner(self, partner):
        # Sync all address fields from partner, or none, to avoid mixing them.
        if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        return values
        
    def _get_partner_email_update(self):
        """Calculate if we should write the email on the related partner. When
        the email of the lead / partner is an empty string, we force it to False
        to not propagate a False on an empty string.

        Done in a separate method so it can be used in both ribbon and inverse
        and compute of email update methods.
        """
        self.ensure_one()
        if self.partner_id and self.email_from != self.partner_id.email:
            lead_email_normalized = tools.email_normalize(self.email_from) or self.email_from or False
            partner_email_normalized = tools.email_normalize(self.partner_id.email) or self.partner_id.email or False
            return lead_email_normalized != partner_email_normalized
        return False

    def _get_partner_phone_update(self):
        """Calculate if we should write the phone on the related partner. When
        the phone of the lead / partner is an empty string, we force it to False
        to not propagate a False on an empty string.

        Done in a separate method so it can be used in both ribbon and inverse
        and compute of phone update methods.
        """
        self.ensure_one()
        if self.partner_id and self.phone != self.partner_id.phone:
            lead_phone_formatted = self._phone_format(fname='phone') or self.phone or False
            partner_phone_formatted = self.partner_id._phone_format(fname='phone') or self.partner_id.phone or False
            return lead_phone_formatted != partner_phone_formatted
        return False

    @api.depends('email_from', 'partner_id')
    def _compute_partner_email_update(self):
        for lead in self:
            lead.partner_email_update = lead._get_partner_email_update()
            
    @api.depends('phone', 'partner_id')
    def _compute_partner_phone_update(self):
        for lead in self:
            lead.partner_phone_update = lead._get_partner_phone_update()
            
    def _prepare_partner_name_from_partner(self, partner):
        """ Company name: name of partner parent (if set) or name of partner
        (if company) or company_name of partner (if not a company). """
        partner_name = partner.parent_id.name
        if not partner_name and partner.is_company:
            partner_name = partner.name
        elif not partner_name and partner.company_name:
            partner_name = partner.company_name
        return {'partner_name': partner_name or self.partner_name} 
    
    def _prepare_contact_name_from_partner(self, partner):
        contact_name = False if partner.is_company else partner.name
        return {'contact_name': contact_name or self.contact_name}
    
    @api.depends('company_id')
    def _compute_company_currency(self):
        for lead in self:
            if not lead.company_id:
                lead.company_currency = self.env.company.currency_id
            else:
                lead.company_currency = lead.company_id.currency_id
    # ----------------------------------------------------
    # ------------------- CRUD ---------------------
    # ----------------------------------------------------
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('school.admission') or _('New')

        result = super(Admission, self).create(vals)
        return result

    
    # -------------------------------------------------------
    # ------------------- Button Actions --------------------
    # -------------------------------------------------------
    def action_accept_application(self):
        self.ensure_one()
        self.action_set_won()

        message = self._get_rainbowman_message()
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/web/image/%s/%s/image_1024' % (self.team_id.user_id._name, self.team_id.user_id.id) if self.team_id.user_id.image_1024 else '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        return True

    def action_set_won(self):
        """ Won semantic: probability = 100 (active untouched) """
        self.action_unarchive()
        # group the leads by team_id, in order to write once by values couple (each write leads to frequency increment)
        leads_by_won_stage = {}
        for lead in self:
            won_stages = self._stage_find(domain=[('is_close', '=', True)], limit=None)
            # ABD : We could have a mixed pipeline, with "won" stages being separated by "standard"
            # stages. In the future, we may want to prevent any "standard" stage to have a higher
            # sequence than any "won" stage. But while this is not the case, searching
            # for the "won" stage while alterning the sequence order (see below) will correctly
            # handle such a case :
            #       stage sequence : [x] [x (won)] [y] [y (won)] [z] [z (won)]
            #       when in stage [y] and marked as "won", should go to the stage [y (won)],
            #       not in [x (won)] nor [z (won)]
            stage_id = next((stage for stage in won_stages if stage.sequence > lead.stage_id.sequence), None)
            if not stage_id:
                stage_id = next((stage for stage in reversed(won_stages) if stage.sequence <= lead.stage_id.sequence), won_stages)
            if stage_id in leads_by_won_stage:
                leads_by_won_stage[stage_id] += lead
            else:
                leads_by_won_stage[stage_id] = lead
        for won_stage_id, leads in leads_by_won_stage.items():
            leads.write({'stage_id': won_stage_id.id, 'probability': 100})
        return True
        
    def get_rainbowman_message(self):
        self.ensure_one()
        if self.stage_id.is_won:
            return self._get_rainbowman_message()
        return False

    def _get_rainbowman_message(self):
        if not self.user_id or not self.team_id:
            return False
        if not self.expected_revenue:
            # Show rainbow man for the first won lead of a salesman, even if expected revenue is not set. It is not
            # very often that leads without revenues are marked won, so simply get count using ORM instead of query
            today = fields.Datetime.today()
            user_won_leads_count = self.search_count([
                ('type', '=', 'opportunity'),
                ('user_id', '=', self.user_id.id),
                ('probability', '=', 100),
                ('date_closed', '>=', date_utils.start_of(today, 'year')),
                ('date_closed', '<', date_utils.end_of(today, 'year')),
            ])
            if user_won_leads_count == 1:
                return _('Go, go, go! Congrats for your first deal.')
            return False

        self.flush_model()  # flush fields to make sure DB is up to date
        query = """
            SELECT
                SUM(CASE WHEN user_id = %(user_id)s THEN 1 ELSE 0 END) as total_won,
                MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '30 days' AND user_id = %(user_id)s THEN expected_revenue ELSE 0 END) as max_user_30,
                MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '7 days' AND user_id = %(user_id)s THEN expected_revenue ELSE 0 END) as max_user_7,
                MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '30 days' AND team_id = %(team_id)s THEN expected_revenue ELSE 0 END) as max_team_30,
                MAX(CASE WHEN date_closed >= CURRENT_DATE - INTERVAL '7 days' AND team_id = %(team_id)s THEN expected_revenue ELSE 0 END) as max_team_7
            FROM oe_admission
            WHERE
                type = 'opportunity'
            AND
                active = True
            AND
                probability = 100
            AND
                DATE_TRUNC('year', date_closed) = DATE_TRUNC('year', CURRENT_DATE)
            AND
                (user_id = %(user_id)s OR team_id = %(team_id)s)
        """
        self.env.cr.execute(query, {'user_id': self.user_id.id,
                                    'team_id': self.team_id.id})
        query_result = self.env.cr.dictfetchone()

        message = False
        if query_result['total_won'] == 1:
            message = _('Go, go, go! Congrats for your first deal.')
        elif query_result['max_team_30'] == self.expected_revenue:
            message = _('Boom! Team record for the past 30 days.')
        elif query_result['max_team_7'] == self.expected_revenue:
            message = _('Yeah! Deal of the last 7 days for the team.')
        elif query_result['max_user_30'] == self.expected_revenue:
            message = _('You just beat your personal record for the past 30 days.')
        elif query_result['max_user_7'] == self.expected_revenue:
            message = _('You just beat your personal record for the past 7 days.')
        return message

    def action_set_lost(self, **additional_values):
        """ Lost semantic: probability = 0 or active = False """
        res = self.action_archive()
        if additional_values:
            self.write(dict(additional_values))
        return res

    def action_application_lost(self):
        self.ensure_one()
        active_id = self.env.context.get('admission_id')
        context = {
            'default_type': 'opportunity',
        }
        if active_id:
            context['default_admission_id'] = active_id
        return {
            'name': 'Lost Reason',
            'view_mode': 'form',
            'res_model': 'oe.admission.lost.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    def toggle_active(self):
        """ When archiving: mark probability as 0. When re-activating
        update probability again, for leads and opportunities. """
        res = super(Admission, self).toggle_active()
        activated = self.filtered(lambda lead: lead.active)
        archived = self.filtered(lambda lead: not lead.active)
        if activated:
            activated.write({'lost_reason_id': False})
            activated._compute_probabilities()
        if archived:
            archived.write({'probability': 0})
        return res

    def action_convert_into_application(self):
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        record_ids = self.env[active_model].search([('id','in',active_ids)])
        if self.env[active_model].search_count([('id', 'in', active_ids), ('type', '=', 'opportunity')]) > 0:
            raise UserError("Closed/Dead enquiries cannot be converted into applications.")

        return {
            'name': _('Convert to Applications'),
            'res_model': 'oe.admission.lead2op.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'oe.admission',
                'active_ids': active_ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_schedule_meeting(self, smart_calendar=True):
        """ Open meeting's calendar view to schedule meeting on current opportunity.

            :param smart_calendar: boolean, to set to False if the view should not try to choose relevant
              mode and initial date for calendar view, see ``_get_opportunity_meeting_view_parameters``
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        current_opportunity_id = self.id if self.type == 'opportunity' else False
        action['context'] = {
            'search_default_opportunity_id': current_opportunity_id,
            'default_opportunity_id': current_opportunity_id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_team_id': self.team_id.id,
            'default_name': self.name,
        }

        # 'Smart' calendar view : get the most relevant time period to display to the user.
        if current_opportunity_id and smart_calendar:
            mode, initial_date = self._get_opportunity_meeting_view_parameters()
            action['context'].update({'default_mode': mode, 'initial_date': initial_date})

        return action

    def _get_opportunity_meeting_view_parameters(self):
        """ Return the most relevant parameters for calendar view when viewing meetings linked to an opportunity.
            If there are any meetings that are not finished yet, only consider those meetings,
            since the user would prefer no to see past meetings. Otherwise, consider all meetings.
            Allday events datetimes are used without taking tz into account.
            -If there is no event, return week mode and false (The calendar will target 'now' by default)
            -If there is only one, return week mode and date of the start of the event.
            -If there are several events entirely on the same week, return week mode and start of first event.
            -Else, return month mode and the date of the start of first event as initial date. (If they are
            on the same month, this will display that month and therefore show all of them, which is expected)

            :return tuple(mode, initial_date)
                - mode: selected mode of the calendar view, 'week' or 'month'
                - initial_date: date of the start of the first relevant meeting. The calendar will target that date.
        """
        self.ensure_one()
        meeting_results = self.env["calendar.event"].search_read([('opportunity_id', '=', self.id)], ['start', 'stop', 'allday'])
        if not meeting_results:
            return "week", False

        user_tz = self.env.user.tz or self.env.context.get('tz')
        user_pytz = pytz.timezone(user_tz) if user_tz else pytz.utc

        # meeting_dts will contain one tuple of datetimes per meeting : (Start, Stop)
        # meetings_dts and now_dt are as per user time zone.
        meeting_dts = []
        now_dt = datetime.now().astimezone(user_pytz).replace(tzinfo=None)

        # When creating an allday meeting, whatever the TZ, it will be stored the same e.g. 00.00.00->23.59.59 in utc or
        # 08.00.00->18.00.00. Therefore we must not put it back in the user tz but take it raw.
        for meeting in meeting_results:
            if meeting.get('allday'):
                meeting_dts.append((meeting.get('start'), meeting.get('stop')))
            else:
                meeting_dts.append((meeting.get('start').astimezone(user_pytz).replace(tzinfo=None),
                                   meeting.get('stop').astimezone(user_pytz).replace(tzinfo=None)))

        # If there are meetings that are still ongoing or to come, only take those.
        unfinished_meeting_dts = [meeting_dt for meeting_dt in meeting_dts if meeting_dt[1] >= now_dt]
        relevant_meeting_dts = unfinished_meeting_dts if unfinished_meeting_dts else meeting_dts
        relevant_meeting_count = len(relevant_meeting_dts)

        if relevant_meeting_count == 1:
            return "week", relevant_meeting_dts[0][0].date()
        else:
            # Range of meetings
            earliest_start_dt = min(relevant_meeting_dt[0] for relevant_meeting_dt in relevant_meeting_dts)
            latest_stop_dt = max(relevant_meeting_dt[1] for relevant_meeting_dt in relevant_meeting_dts)

            # The week start day depends on language. We fetch the week_start of user's language. 1 is monday.
            lang_week_start = self.env["res.lang"].search_read([('code', '=', self.env.user.lang)], ['week_start'])
            # We substract one to make week_start_index range 0-6 instead of 1-7
            week_start_index = int(lang_week_start[0].get('week_start', '1')) - 1

            # We compute the weekday of earliest_start_dt according to week_start_index. earliest_start_dt_index will be 0 if we are on the
            # first day of the week and 6 on the last. weekday() returns 0 for monday and 6 for sunday. For instance, Tuesday in UK is the
            # third day of the week, so earliest_start_dt_index is 2, and remaining_days_in_week includes tuesday, so it will be 5.
            # The first term 7 is there to avoid negative left side on the modulo, improving readability.
            earliest_start_dt_weekday = (7 + earliest_start_dt.weekday() - week_start_index) % 7
            remaining_days_in_week = 7 - earliest_start_dt_weekday

            # We compute the start of the week following the one containing the start of the first meeting.
            next_week_start_date = earliest_start_dt.date() + timedelta(days=remaining_days_in_week)

            # Latest_stop_dt must be before the start of following week. Limit is therefore set at midnight of first day, included.
            meetings_in_same_week = latest_stop_dt <= datetime(next_week_start_date.year, next_week_start_date.month, next_week_start_date.day, 0, 0, 0)

            if meetings_in_same_week:
                return "week", earliest_start_dt.date()
            else:
                return "month", earliest_start_dt.date()

    # Partner/Student Creation and assignment
    def _handle_student_assignment(self, force_partner_id=False, create_missing=True):
        """ Update student (partner_id) of leads. Purpose is to set the same
        partner on most leads; either through a newly created partner either
        through a given partner_id.

        :param int force_partner_id: if set, update all leads to that customer;
        :param create_missing: for leads without customer, create a new one
          based on lead information;
        """
        for admission in self:
            if force_partner_id:
                admission.partner_id = force_partner_id
            if not admission.partner_id and create_missing:
                partner = admission._create_student()
                admission.partner_id = partner.id

    def _get_application_duplicates(self, partner=None, email=None, include_lost=False):
        """ Search for leads that seem duplicated based on partner / email.

        :param partner : optional customer when searching duplicated
        :param email: email (possibly formatted) to search
        :param boolean include_lost: if True, search includes archived opportunities
          (still only active leads are considered). If False, search for active
          and not won leads and opportunities;
        """
        if not email and not partner:
            return self.env['oe.admission']

        domain = []
        for normalized_email in [tools.email_normalize(email) for email in tools.email_split(email)]:
            domain.append(('email_normalized', '=', normalized_email))
        if partner:
            domain.append(('partner_id', '=', partner.id))

        if not domain:
            return self.env['oe.admission']

        domain = ['|'] * (len(domain) - 1) + domain
        if include_lost:
            domain += ['|', ('type', '=', 'opportunity'), ('active', '=', True)]
        else:
            domain += ['&', ('active', '=', True), '|', ('stage_id', '=', False), ('stage_id.is_won', '=', False)]
            
        return self.with_context(active_test=False).search(domain)
        
    def _find_matching_partner(self, email_only=False):
        """ Try to find a matching partner with available information on the
        lead, using notably customer's name, email, ...

        :param email_only: Only find a matching based on the email. To use
            for automatic process where ilike based on name can be too dangerous
        :return: partner browse record
        """
        self.ensure_one()
        partner = self.partner_id

        if not partner and self.email_from:
            partner = self.env['res.partner'].search([('email', '=', self.email_from)], limit=1)

        if not partner and not email_only:
            # search through the existing partners based on the lead's partner or contact name
            # to be aligned with _create_customer, search on lead's name as last possibility
            for customer_potential_name in [self[field_name] for field_name in ['partner_name', 'contact_name', 'name'] if self[field_name]]:
                partner = self.env['res.partner'].search([('name', 'ilike', '%' + customer_potential_name + '%')], limit=1)
                if partner:
                    break

        return partner
        
    def _create_student(self):
        """ Create a partner from lead data and link it to the lead.

        :return: newly-created partner browse record
        """
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name:
            partner_company = Partner.create(self._prepare_student_values(self.partner_name, is_company=True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        if contact_name:
            return Partner.create(self._prepare_student_values(contact_name, is_company=False, parent_id=partner_company.id if partner_company else False))

        if partner_company:
            return partner_company
        return Partner.create(self._prepare_student_values(self.name, is_company=False))

    def _prepare_student_values(self, partner_name, is_company=False, parent_id=False):
        """ Extract data from lead to create a partner.

        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        email_parts = tools.email_split(self.email_from)
        res = {
            'name': partner_name,
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'admission_team_id': self.team_id.id,
            'is_student': True,
            'course_id': self.course_id.id,
            'batch_id': self.batch_id.id,
            'section_id': self.section_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_parts[0] if email_parts else False,
            'title': self.title.id,
            #'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'website': self.website,
            'is_company': is_company,
            'type': 'contact'
        }
        if self.lang_id:
            res['lang'] = self.lang_id.code
        return res
        
    # ------------ Actions -----------------------------
    def action_convert_application(self):
         return {
            'name': 'Convert into Application',
            'view_mode': 'form',
            'res_model': 'oe.admission.lead2op.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_confirm_admission(self):
        active_ids = self.env.context.get('active_ids', [])
        current_record = 0
        try:
            current_record = self.id
        except:
            current_record = 0
        
        admission_ids = self.env['oe.admission'].search(['|', ('id', 'in', active_ids), ('id', '=', current_record)])

        course_id = admission_ids.mapped('course_id')
        #raise UserError(admission_ids)
        
        if len(course_id) != 1:
            raise UserError('Please note that admission confirmation is limited to one course at a time.')
        if any(admission.admission_confirmed for admission in admission_ids):
            raise UserError(_("One or more selected application are already confirmed."))
            
        return {
            'name': 'Confirm Admission',
            'view_mode': 'form',
            'res_model': 'oe.admission.confirm.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'course_id': course_id.id,
                'use_batch': course_id.use_batch_subject,
                'use_section': course_id.use_section,
            }
        }
        
    def open_enrollment_history(self):
        admission_enrollment_ids = self.env['oe.school.student.enrollment'].search([
            ('model','=',self._name),
            ('res_id','=',self.id)
        ])
        partner_enrollment_ids = self.env['oe.school.student.enrollment'].search([
            ('model','=','res.partner'),
            ('res_id','=',self.partner_id.id)
        ])
        enrollment_ids = admission_enrollment_ids.mapped('id') + partner_enrollment_ids.mapped('id')
            
        #raise UserError(enrollment_ids)
        action = self.env.ref('de_school.action_enrollment_history').read()[0]
        action.update({
            'name': 'Enrollment History',
            'view_mode': 'tree',
            'res_model': 'oe.school.student.enrollment',
            'type': 'ir.actions.act_window',
            'domain': [
               ('id','in',enrollment_ids),
               # ('model','=','res.partner'),
            ],
            'context': {
                'default_model': self._name,
                'default_res_id': self.id,
            },
        })
        if self.admission_confirmed:
            action['context'].update({
                'create': False,
                'delete': False,
                'edit': False,
            })
            
        return action
        