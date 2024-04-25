# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta, date
from odoo import api, fields, models, _
from odoo.tools import float_compare, format_datetime, format_time
from pytz import timezone, UTC
from odoo.exceptions import ValidationError, UserError


class EnrollmentContract(models.Model):
    _inherit = 'sale.order'

    is_enrol_order = fields.Boolean("Enrol Order")
    enrol_status = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'In Progress'), 
        ('open', 'Running'), #The student is officially enrolled and attending classes.
        ('close', 'Close'), #close the contract, student completed the course.
        ('paused', 'Paused'),
        ('cancel', 'Cancelled'), #student decides not to enroll after initially submitting the agreement,
        ('expire', 'Expired'), #Some enrollment agreements may have an expiration date, if that date passes without acceptance, the status could be "Expired.
    ], string="Enroll Status", default='draft', 
                store=True, tracking=True, index=True,
                compute='_compute_enrol_status',
            )
    # enroll_status = next action to do basically, but shown string is action done.
    
    # Academic Fields
    course_id = fields.Many2one('oe.school.course', string='Course')
    use_batch = fields.Boolean(related='course_id.use_batch_subject')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(related='course_id.use_section')
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                                 domain="[('course_id','=',course_id)]"
                              )
    
    admission_team_id = fields.Many2one(
        comodel_name='oe.admission.team',
        string="Admission Team",
        compute='_compute_admission_team_id',
        store=True, readonly=False, precompute=True, ondelete="set null",
        change_default=True, check_company=True,  # Unrequired company
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    roll_no = fields.Char(related='partner_id.roll_no', readonly=False)
    roll_no_assigned = fields.Boolean(string='Roll Number Assigned', default=False, compute='_compute_rollno_assignment')
                              
    @api.onchange('enrol_order_tmpl_id')
    def _onchange_enrol_order_tmpl_id(self):
        enrol_order_template = self.enrol_order_tmpl_id.with_context(lang=self.partner_id.lang)

        order_lines_data = [fields.Command.clear()]
        order_lines_data += [
            fields.Command.create(line._prepare_order_line_values())
            for line in enrol_order_template.enrol_order_tmpl_line
        ]

        # set first line to sequence -99, so a resequence on first page doesn't cause following page
        # lines (that all have sequence 10 by default) to get mixed in the first page
        if len(order_lines_data) >= 2:
            order_lines_data[1][2]['sequence'] = -99

        self.order_line = order_lines_data

    @api.depends('partner_id', 'user_id')
    def _compute_admission_team_id(self):
        cached_teams = {}
        for order in self:
            default_team_id = self.env.context.get('default_admission_team_id', False) or order.admission_team_id.id or order.partner_id.admission_team_id.id
            user_id = order.user_id.id
            company_id = order.company_id.id
            key = (default_team_id, user_id, company_id)
            if key not in cached_teams:
                cached_teams[key] = self.env['oe.admission.team'].with_context(
                    default_team_id=default_team_id
                )._get_default_team_id(
                    user_id=user_id, domain=[('company_id', 'in', [company_id, False])])
            order.admission_team_id = cached_teams[key]

    @api.depends(
        'state',
        'invoice_ids',
                )
    def _compute_enrol_status(self):
        for record in self:
            if record.enrol_status == 'progress' and len(record.invoice_ids.filtered(lambda x:x.state != 'cancel')) > 0:
                record.enrol_status = 'open'
            elif record.state == 'cancel':
                record.enrol_status = 'cancel'

    def _compute_rollno_assignment(self):
        for record in self:
            if record.roll_no:
                record.roll_no_assigned = True
            else:
                record.roll_no_assigned = False
                
    #=== CRUD METHODS ===#
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if vals.get('name', _("New")) == _("New"):
                if vals.get('is_enrol_order', False):
                    # Assign a new sequence for enrol orders
                    seq_date = fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals.get('date_order')) if 'date_order' in vals else None
                    )
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'enrol.order', sequence_date=seq_date) or _("New")
                else:
                    # Use the default sequence and state for non-enrol orders
                    seq_date = fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals.get('date_order')) if 'date_order' in vals else None
                    )
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'sale.order', sequence_date=seq_date) or _("New")
                    vals['state'] = 'draft'  # Set the state to 'draft' (or another appropriate state)

        return super(EnrollmentContract, self).create(vals_list)

        
    # =========================================================================
    # ============================ Action Button ==============================
    # =========================================================================
    def action_confirm(self):
        """Update and/or create enrollment on order confirmation."""
        for order in self:
            if order.is_enrol_order:
                if any(not line.product_id.fee_product for line in order.order_line):
                    raise UserError(_("Only Fee Products are allowed for enrollment orders."))
                    
            res = super(EnrollmentContract, self).action_confirm()
            order.write({
                'enrol_status': 'progress',
            })
            return res

    def start_contract(self):
        for order in self:
            order.enrol_status = 'open'

    def assign_roll_number(self):
        active_ids = self.env.context.get('active_ids', [])
        current_record = 0
        try:
            current_record = self.id
        except:
            current_record = 0

        order_ids = self.env['sale.order'].search(['|',
            ('id','in',active_ids),
            ('id','=',current_record),
        ])
        for record in order_ids.filtered(lambda x: not x.roll_no_assigned):
            record.roll_no = record.course_id.sequence_id.next_by_id()
            record.roll_no_assigned = True
    
    def button_submit(self):
        self.write({
            'enrol_status': 'submit'
        })

    def button_start_review(self):
        self.write({
            'enrol_status': 'review'
        })

    def button_end_review(self):
        self.write({
            'enrol_status': 'approved'
        })
        
    def button_interview(self):
        self.write({
            'enrol_status': 'pending'
        })

    def button_payment(self):
        self.write({
            'enrol_status': 'done'
        })

    def button_confirm(self):
        self.write({
            'enrol_status': 'open'
        })
class EnrollmentOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_enrol = fields.Boolean(default=False)  # change to compute if pickup_date and return_date set?

   