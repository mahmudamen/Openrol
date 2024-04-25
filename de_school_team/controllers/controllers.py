# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolTeams(http.Controller):
#     @http.route('/de_school_teams/de_school_teams', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_teams/de_school_teams/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_teams.listing', {
#             'root': '/de_school_teams/de_school_teams',
#             'objects': http.request.env['de_school_teams.de_school_teams'].search([]),
#         })

#     @http.route('/de_school_teams/de_school_teams/objects/<model("de_school_teams.de_school_teams"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_teams.object', {
#             'object': obj
#         })
