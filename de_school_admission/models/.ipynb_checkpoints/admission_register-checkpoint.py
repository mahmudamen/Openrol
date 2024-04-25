# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, SUPERUSER_ID, _


class AdmissionRegister(models.Model):
    _name = "oe.admission.register"
    _description = "Admission Register"
    _order = "name asc"
    
    active = fields.Boolean(default=True)
    name = fields.Char(string='Name', required=True, index='trigram', translate=True)
    school_year_id = fields.Many2one('oe.school.year',string='Academic Year')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    max_students = fields.Integer(string='Maximum Admissions', store=True,
                                        help='Expected number of students for this course after new admission.')
    min_students = fields.Integer(string="Current Number of Employees", store=True, 
                                  help='Number of minimum students expected for this course.')
    no_of_applicants = fields.Integer(string='Total Applicants', copy=False,
        help='Number of new applications you expect to enroll.', default=1)
    no_of_enrolled = fields.Integer(string='Total Enrolled', copy=False,
        help='Number of new admission you expect to enroll.', default=1)
        
    description = fields.Html(string='Job Description')
    requirements = fields.Text('Requirements')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    course_id = fields.Many2one('oe.school.course', string='Course', required=True)
