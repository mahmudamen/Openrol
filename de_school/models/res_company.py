# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import logging
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path

from random import randrange
from PIL import Image

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = "res.company"
    
    is_school = fields.Boolean(string='School')
    school_type = fields.Selection(
        [
            ('k12','K12 School'),
            ('col','College'),
            ('uni','University'),
            ('ti','Vocational/Technical Institute'),
            ('ling','Language Learning Center'),
            ('art','Art School'),
            ('special','Special Needs School'),
        ],
        default='k12', string='School Type',
    )
    use_batch = fields.Boolean('Enable Batch')
    use_section = fields.Boolean('Enable Section')
    use_credit_hours = fields.Boolean('Enable Credit Hours')
    