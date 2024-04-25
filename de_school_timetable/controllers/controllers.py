# -*- coding: utf-8 -*-
# from odoo import http


# class DeSchoolTimetable(http.Controller):
#     @http.route('/de_school_timetable/de_school_timetable', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_school_timetable/de_school_timetable/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_school_timetable.listing', {
#             'root': '/de_school_timetable/de_school_timetable',
#             'objects': http.request.env['de_school_timetable.de_school_timetable'].search([]),
#         })

#     @http.route('/de_school_timetable/de_school_timetable/objects/<model("de_school_timetable.de_school_timetable"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_school_timetable.object', {
#             'object': obj
#         })
