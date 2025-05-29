# -*- coding: utf-8 -*-

from odoo import models, fields, _


class User(models.Model):
    _inherit = 'res.users'
    
    loc_area_1_ids = fields.One2many('area.level.1', 'manager_id', 'Location Area 1s', readonly=True, copy=False)
    resposible_farmer_ids = fields.Many2many('res.partner', string='Farmers Responsible', compute='_compute_resposible_farmer_ids')
    
    def _compute_resposible_farmer_ids(self):
        for user in self:
            user.resposible_farmer_ids = user.loc_area_1_ids.farmer_group_ids.member_ids
    