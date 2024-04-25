# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from bs4 import BeautifulSoup

class TicketMergeWizard(models.TransientModel):
    _name = 'oe.exam.attendees.attend'
    _description = 'Ticket Reopen Wizard'

    exam_attendee_ids = fields.Many2many(
        'oe.exam.attendees', default=lambda self: self.env.context.get('active_ids'))
    
    status = fields.Selection([
        ('P', 'Present'),
        ('A', 'Absent'),
    ], string='Status', 
    )

    def action_apply_attendance(self):
        for attendee in self.exam_attendee_ids:
            attendee.write({
                'status': self.status,
            })