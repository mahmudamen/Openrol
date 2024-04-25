# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolAdmission(http.Controller):
#     @http.route('/de_school_admission/de_school_admission', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_admission/de_school_admission/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_admission.listing', {
#             'root': '/de_school_admission/de_school_admission',
#             'objects': http.request.env['de_school_admission.de_school_admission'].search([]),
#         })

#     @http.route('/de_school_admission/de_school_admission/objects/<model("de_school_admission.de_school_admission"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_admission.object', {
#             'object': obj
#         })
