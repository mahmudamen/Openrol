# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchool(http.Controller):
#     @http.route('/de_school/de_school/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school/de_school/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school.listing', {
#             'root': '/de_school/de_school',
#             'objects': http.request.env['de_school.de_school'].search([]),
#         })

#     @http.route('/de_school/de_school/objects/<model("de_school.de_school"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school.object', {
#             'object': obj
#         })
