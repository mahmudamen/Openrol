# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolExam(http.Controller):
#     @http.route('/de_school_exam/de_school_exam', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_exam/de_school_exam/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_exam.listing', {
#             'root': '/de_school_exam/de_school_exam',
#             'objects': http.request.env['de_school_exam.de_school_exam'].search([]),
#         })

#     @http.route('/de_school_exam/de_school_exam/objects/<model("de_school_exam.de_school_exam"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_exam.object', {
#             'object': obj
#         })
