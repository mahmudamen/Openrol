# -*- coding: utf-8 -*-
import json
import random
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.safe_eval import safe_eval

class AdmissionTeam(models.Model):
    _inherit = "oe.admission.team"

    opportunities_count = fields.Integer(
        string='# Opportunities', compute='_compute_opportunities_data')
    opportunities_amount = fields.Monetary(
        string='Opportunities Revenues', compute='_compute_opportunities_data')
    
    count_loan_to_pay = fields.Integer(string='Loan Confirm')
    priority = fields.Integer(string='Priority')
    stage_id = fields.Integer(string='stage')

    dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')
    dashboard_graph_data = fields.Text(compute='_compute_dashboard_graph')

    is_application_revenue = fields.Boolean(string='Allow Expected Revenue', compute='_compute_admission_setting_values')

    def _compute_admission_setting_values(self):
        application_revenue = self.env['ir.config_parameter'].sudo().get_param('de_school_admission.is_application_revenue', False)
        for record in self:
            record.is_application_revenue = application_revenue

    def _graph_get_model(self):
        return 'oe.admission'

    def _graph_y_query(self):
        return 'count(*)'
        #return super(AdmissionTeam,self)._graph_y_query()

    def _compute_dashboard_graph(self):
        for team in self:
            team.dashboard_graph_data = json.dumps(team._get_dashboard_graph_data())

    def _compute_opportunities_data(self):
        opportunity_data = self.env['oe.admission']._read_group([
            ('team_id', 'in', self.ids),
            ('probability', '<', 100),
            ('type', '=', 'opportunity'),
        ], ['team_id'], ['__count', 'expected_revenue:sum'])
        counts_amounts = {team.id: (count, expected_revenue_sum) for team, count, expected_revenue_sum in opportunity_data}
        for team in self:
            team.opportunities_count, team.opportunities_amount = counts_amounts.get(team.id, (0, 0))
            
    # -----------------------------------------------------------------
    # ----------------------- Action buttons- --------------------------
    # ------------------------------------------------------------------
    def action_open_team_admissions_all(self):
        self.ensure_one()
        active_id = self.env.context.get('team_id')
        context = {
            'default_type': 'opportunity',
        }
        if active_id:
            context['search_default_team_id'] = [active_id]
            context['default_team_id'] = active_id
        return {
            'name': 'Applications',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'oe.admission',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': [('team_id','=',self.id),('type','=','opportunity')],
        }
    
    def action_open_new_admissions(self):
        self.ensure_one()
        active_id = self.env.context.get('team_id')
        context = {
            'default_type': 'opportunity',
        }
        if active_id:
            context['search_default_team_id'] = [active_id]
            context['default_team_id'] = active_id
        return {
            'name': 'Application',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'oe.admission',
            'type': 'ir.actions.act_window',
            'context': context,
        }

    def action_open_applications(self):
        self.ensure_one()
        active_id = self.env.context.get('team_id')
        context = {
            'default_type': 'opportunity',
            'default_team_id': active_id,
            'search_default_open_opportunities': True,
        }
        if active_id:
            context['search_default_team_id'] = [active_id]
            context['default_team_id'] = active_id
        return {
            'name': 'Overdue',
            'view_type': 'form',
            'view_mode': 'kanban,tree,graph,form,calendar,pivot',
            'res_model': 'oe.admission',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': [('team_id','=',self.id),('type','=','opportunity')],
        }
        
    def action_open_overdue_applications(self):
        self.ensure_one()
        active_id = self.env.context.get('team_id')
        context = {
            'default_type': 'opportunity',
            'search_default_overdue_opp': 1,
            'default_user_id': self.env.user,
        }
        if active_id:
            context['search_default_team_id'] = [active_id]
            context['default_team_id'] = active_id
        return {
            'name': 'Overdue',
            'view_type': 'form',
            'view_mode': 'kanban,tree,graph,form,calendar,pivot',
            'res_model': 'oe.admission',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': [('team_id','=',self.id),('type','=','opportunity')],
        }
        
    def action_report_admission_analysis(self):
        self.ensure_one()
        active_id = self.env.context.get('team_id')
        context = {
            'default_type': 'opportunity',
        }
        if active_id:
            context['search_default_team_id'] = [active_id]
            context['default_team_id'] = active_id
            context['search_default_admissionteam'] = active_id
        return {
            'name': 'Analysis',
            'view_mode': 'graph,pivot,tree,form',
            'res_model': 'oe.admission',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': [('team_id','=',self.id),('type','=','opportunity')],
            'res_id': self.id,
            'action_id': self.env.ref('de_school_admission.admission_report_action').id,
        }
        
    def admission_activity_report_action_team(self):
        self.ensure_one()
        return {
            'name': 'Admission Activities',
            'view_mode': 'graph,pivot,tree',
            'res_model': 'oe.admission.activity.report',
            'type': 'ir.actions.act_window',
        }
        
    def action_admin_config(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [[False, "form"]],
            'res_model': 'oe.admission.team',
            'res_id': self.id,
        }

    def action_edit_admissions_team(self):
        return {
           'name': 'Admission Team',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'oe.admission.team',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def action_admission_pipeline(self):
        action = self.env["ir.actions.actions"]._for_xml_id("de_school_admission.action_admission_application_pipeline")
        return self._action_update_to_pipeline(action)

    @api.model
    def _action_update_to_pipeline(self, action):
        user_team_id = self.env.user.admission_team_id.id
        if user_team_id:
            # To ensure that the team is readable in multi company
            user_team_id = self.search([('id', '=', user_team_id)], limit=1).id
        else:
            user_team_id = self.search([], limit=1).id
            action['help'] = "<p class='o_view_nocontent_smiling_face'>%s</p><p>" % _("Create an Opportunity")
            if user_team_id:
                if self.user_has_groups('de_school_team.group_school_admission_manager'):
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Admission Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the Admission, you should <a name="%d" type="action" tabindex="-1">join a team.</a>""",
                                        self.env.ref('de_school_team.action_school_team_config').id)
                else:
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Admission Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the Admission, you should join a team.""")
        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id

        #raise UserError(user_team_id)
        action['context'] = action_context
        return action