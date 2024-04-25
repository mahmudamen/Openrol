# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolAssignment(http.Controller):
#     @http.route('/de_school_assignment/de_school_assignment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_assignment/de_school_assignment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_assignment.listing', {
#             'root': '/de_school_assignment/de_school_assignment',
#             'objects': http.request.env['de_school_assignment.de_school_assignment'].search([]),
#         })

#     @http.route('/de_school_assignment/de_school_assignment/objects/<model("de_school_assignment.de_school_assignment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_assignment.object', {
#             'object': obj
#         })
