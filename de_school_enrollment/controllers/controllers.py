# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolEnrollment(http.Controller):
#     @http.route('/de_school_enrollment/de_school_enrollment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_enrollment/de_school_enrollment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_enrollment.listing', {
#             'root': '/de_school_enrollment/de_school_enrollment',
#             'objects': http.request.env['de_school_enrollment.de_school_enrollment'].search([]),
#         })

#     @http.route('/de_school_enrollment/de_school_enrollment/objects/<model("de_school_enrollment.de_school_enrollment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_enrollment.object', {
#             'object': obj
#         })
