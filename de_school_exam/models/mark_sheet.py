# -*- coding: utf-8 -*-

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class MarkSheet(models.Model):
    _name = 'oe.exam.marksheet'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Mark Sheet'

    name = fields.Char(
        string="Reference",
        copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('/'))

    domain_exam_session_ids = fields.Many2many(
        comodel_name='oe.exam.session',
        string='Open Sessions',
        compute='_compute_domain_exam_sessions',
    )
    
    exam_session_ids = fields.Many2many(
        comodel_name='oe.exam.session',
        relation='exam_session_mark_sheet_rel',  # Custom relation name
        column1='mark_sheet_id',  # Column name for this model
        column2='exam_session_id',  # Column name for the related model
        string="Exam Sessions",  # Field label
        copy=False,  # Copy behavior
        compute='_compute_domain_exam_sessions',
        store=True,
        domain="[('id','in',domain_exam_session_ids)]"
    )

    student_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('is_student','=',True)]",
        string="Student", required=True, 
        change_default=True, ondelete='restrict', 
    )

    roll_no = fields.Char(related='student_id.roll_no')
    batch_id = fields.Many2one(related='student_id.batch_id')
    section_id = fields.Many2one(related='student_id.section_id')

    marksheet_group_id = fields.Many2one(
        comodel_name='oe.exam.msheet.group',
        string="Marksheet Group", required=True,  
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Generated'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company
    )
    
    marksheet_line = fields.One2many('oe.exam.marksheet.line', 'marksheet_id', string='Mark Sheet', )
    dynamic_view_arch = fields.Html(string='view code')
    # Constrains
    @api.constrains('exam_session_id', 'student_id', 'state')
    def _check_unique_marksheet(self):
        domain = [
                ('exam_session_ids', 'in', self.exam_session_ids.ids),
                ('student_id', '=', self.student_id.id),
                ('state', '=', ['draft','done']),
                ('id', '!=', self.id),
        ]
        if self.search_count(domain) > 0:
            raise exceptions.ValidationError(_('Mark Sheet must be unique per session for a student.'))

    # -----------------------------------------------------------------------------
    # ------------------------------ CRUD Operations ------------------------------ 
    # -----------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        sheets = super(MarkSheet, self).create(vals_list)
        for sheet in sheets:
            sheet.name = self.env['ir.sequence'].next_by_code('marksheet.sequence')            
        return sheets
        
    # Compute Methods
    @api.depends('marksheet_group_id')
    def _compute_domain_exam_sessions(self):
        for record in self:
            if record.marksheet_group_id:
                exam_type_ids = record.marksheet_group_id.ms_group_line.mapped('exam_type_id')
                exams = self.env['oe.exam.session'].search([
                    ('state', '=', 'progress'),
                    ('exam_line', '!=', False),
                    ('exam_type_id', 'in', exam_type_ids.ids),
                    ('company_id','=', record.company_id.id),
                ])
                record.domain_exam_session_ids = [(6, 0, exams.ids)]
            else:
                record.domain_exam_session_ids = [(5, 0, 0)]  # 
    
    # Actions
    def button_draft(self):
        record.write({
            'state': 'draft'
        })

    def button_generate(self):
        self._generate_marksheet()
        self._action_post()

    def _action_post(self):
        for record in self:
            record.write({
                'state': 'done'
            })

    @api.model
    def _generate_marksheet(self):
        self.marksheet_line.unlink()
        self.env['oe.exam.ms.line.score'].search([('marksheet_line_id.marksheet_id', '=', self.id)]).unlink()

        subject_ids = self.env['oe.exam'].search(self._exam_domain()).mapped('subject_id')

        marksheet_lines = self.env['oe.exam.marksheet.line'].create([
            {'subject_id': subject.id, 'marksheet_id': self.id} for subject in subject_ids
        ])

        score_lines = []
        for marksheet_line in marksheet_lines:
            score_lines += self._create_score_line(marksheet_line)

        self.env['oe.exam.ms.line.score'].create(score_lines)
        self.dynamic_view_arch = self._compute_dynamic_view_arch()
        
    def _exam_domain(self):
        domain = [
            ('exam_session_id','in',self.exam_session_ids.ids),
            ('state','=','done'),
            #('exam_session_id.exam_type_id','in', self.marksheet_group_id.ms_group_line.mapped('exam_type_id').ids)
        ]
        return domain

    def _create_score_line(self, marksheet_line):
        score_lines = []
        for type in self.exam_session_ids.mapped('exam_type_id'):
            score_vals = {
                'marksheet_line_id': marksheet_line.id,
                'exam_type_id': type.id,
                'marks': self._compute_marksheet_value(marksheet_line.subject_id, type),
            }
            score_lines.append(score_vals)
        return score_lines

    @api.model
    def _compute_marksheet_value(self, subject, exam_type_id):
        exam_results = self.env['oe.exam.result'].search([
            ('exam_id.exam_session_id.exam_type_id', '=', exam_type_id.id),
            ('exam_id.subject_id', '=', subject.id),
            ('student_id', '=', self.student_id.id),
        ])
        total_marks = sum(exam_results.mapped('marks'))
        return total_marks

    def button_cancel(self):
        record.write({
            'state': 'cancel'
        })

    def _compute_dynamic_view_arch(self):
        arch = ''
        for ms in self:
            
            # Construct the dynamic arch
            arch += "<div class='o_field_widget o_field_section_and_note_one2many o_field_one2many'>"
            arch += "<div class='o_list_view o_field_x2many o_field_x2many_list'>"
            arch += "<div class='o_list_renderer o_renderer table-responsive o_list_renderer_2' style='position:absolute;top:0;left:0;'>"
            arch += "<table class='o_section_and_note_list_view o_list_table table table-sm table-hover position-relative mb-0 o_list_table_ungrouped table-striped' style='table-layout: fixed;'>"
            arch += "<thead>"
            arch += "<tr>"

            # field Labels
            arch += '<th data-tooltip-delay="1000" tabindex="2" data-name="subject_id" class="align-middle o_column_sortable position-relative cursor-pointer o_section_and_note_text_cell opacity-trigger-hover" style="width: 94px;">'
            arch += '<span class="d-block min-w-0 text-truncate flex-grow-1">'
            arch += 'Subject'
            arch += '</span>'
            arch += '</th>'
            for group in ms.marksheet_group_id.ms_group_line:
                arch += '<th data-tooltip-delay="1000" tabindex="-1" data-name="name" class="aalign-middle o_column_sortable position-relative cursor-pointer o_list_number_th opacity-trigger-hover" style="min-width: 104px; width: 104px;">'
                arch += '<div class="d-flex flex-row-reverse">'
                arch += '<span class="d-block min-w-0 text-truncate flex-grow-1 o_list_number_th">'
                arch += group.exam_type_id.name
                arch += '</span>'
                arch += '</div>'
                arch += '</th>'

            arch += '<th data-tooltip-delay="1000" tabindex="-1" data-name="name" class="aalign-middle o_column_sortable position-relative cursor-pointer o_list_number_th opacity-trigger-hover" style="min-width: 104px; width: 104px;">'
            arch += '<div class="d-flex flex-row-reverse">'
            arch += '<span class="d-block min-w-0 text-truncate flex-grow-1 o_list_number_th">'
            arch += 'Total'
            arch += '</span>'
            arch += '</div>'
            arch += '</th>'
            
            arch += '</tr>'
            arch += '</thead>'
            arch += '<tbody>'

            for line in ms.marksheet_line:
                arch += '<tr class="o_data_row o_is_false">'
                arch += '<td class="o_data_cell cursor-pointer o_field_cell o_list_text o_section_and_note_text_cell o_required_modifier">'
                arch += '<div class="o_field_widget o_required_modifier o_field_section_and_note_text o_field_text">'
                arch += line.subject_id.name
                arch += '</div>'
                arch += '</td>'

                for group in ms.marksheet_group_id.ms_group_line:
                    for score in line.marksheet_line_score_ids.filtered(lambda x:x.exam_type_id.id == group.exam_type_id.id):
                        arch += '<td class="o_data_cell cursor-pointer o_field_cell o_list_number o_readonly_modifier">'
                        arch += str(score.marks)
                        arch += '</td>'

                arch += '<td class="o_data_cell cursor-pointer o_field_cell o_list_number o_readonly_modifier">'
                arch += str(line.marks_total)
                arch += '</td>'
                arch += '</tr>'
            arch += '</tbody>'
            arch += '</table>'
            arch += '</div>'
            arch += '</div>'
            arch += '</div>'
        return arch
            
class MarkSheetLine(models.Model):
    _name = 'oe.exam.marksheet.line'
    _description = 'Marksheet Line'

    marksheet_id = fields.Many2one(
        comodel_name='oe.exam.marksheet',
        string="Mark Sheet", 
        required=True, ondelete='cascade', index=True, copy=False)
    subject_id = fields.Many2one('oe.school.subject', string='Subject',
                                 required=True,
                                )

    marksheet_line_score_ids = fields.One2many('oe.exam.ms.line.score', 'marksheet_line_id', string='Subject Scores', )
    marks_total = fields.Float('Total Marks', compute='_compute_marks_total')

    #@api.depends(
    #    'marksheet_line_score_ids', 
    #    'marksheet_line_score_ids.marks', 
    #    'marksheet_line_score_ids.exam_type_id.grade_weightage'
    #)
    def _compute_marks_total(self):
        group_line_id = self.env['oe.exam.msheet.group.line']
        for line in self:
            total_marks = 0.0
            total_weightage = 0.0
            
            for score in line.marksheet_line_score_ids:
                group_line_id = self.env['oe.exam.msheet.group.line'].search([
                    ('ms_group_id','=', line.marksheet_id.marksheet_group_id.id),
                    ('exam_type_id','=', score.exam_type_id.id),
                ])
                
                total_marks += score.marks * (group_line_id.grade_weightage/100)
            line.marks_total = round(total_marks,2)

class MarkSheetLineScore(models.Model):
    _name = 'oe.exam.ms.line.score'
    _description = 'Marksheet Subject Score'

    marksheet_line_id = fields.Many2one(
        comodel_name='oe.exam.marksheet.line',
        string="Mark Sheet Line", 
        required=True, ondelete='cascade', index=True, copy=False)
    exam_type_id = fields.Many2one('oe.exam.type', string='Exam Type', required=True)
    marks = fields.Float(string='Marks', required=True)
