# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError

class RoomAllocation(models.TransientModel):
    _name = 'oe.school.tt.room.alloc.wizard'
    _description = 'Room Allocation Wizard'
 
    timetable_ids = fields.Many2many(
        'oe.school.timetable', default=lambda self: self.env.context.get('active_ids'))
    
    classroom_id = fields.Many2one('oe.school.building.room', string='Classroom', 
                                  store=True, readonly=False, required=True
                                 )

    def action_room_allocation(self):
        for tt in self.timetable_ids:
            tt.write({
                'classroom_id': self.classroom_id.id,
            })