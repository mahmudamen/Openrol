# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolAdmissionEnrol(http.Controller):
#     @http.route('/de_school_admission_enrol/de_school_admission_enrol', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_admission_enrol/de_school_admission_enrol/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_admission_enrol.listing', {
#             'root': '/de_school_admission_enrol/de_school_admission_enrol',
#             'objects': http.request.env['de_school_admission_enrol.de_school_admission_enrol'].search([]),
#         })

#     @http.route('/de_school_admission_enrol/de_school_admission_enrol/objects/<model("de_school_admission_enrol.de_school_admission_enrol"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_admission_enrol.object', {
#             'object': obj
#         })
