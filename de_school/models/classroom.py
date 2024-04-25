# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class ClassroomBuilding(models.Model):
    _name = 'oe.school.building'
    _description = 'School Building'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Building", required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    address_id = fields.Many2one('res.partner', required=True, string="Building Address", domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
        
class ClassroomBuildingRoom(models.Model):
    _name = 'oe.school.building.room'
    _description = 'Classrooms'
    _order = 'name'
    
    name = fields.Char(string='Room Name', required=True, index=True, translate=True)
    building_id = fields.Many2one('oe.school.building', string='Building', required=True, index=True, )
    capacity = fields.Integer(string='Capacity', required=True, default=10)

