# -*- coding: utf-8 -*-

from odoo import models, fields, _


class User(models.Model):
    _inherit = 'res.users'
    
    cooperative_ids = fields.One2many('cooperative', 'community_facilitator_id', 'Cooperatives', readonly=True, copy=False)
    resposible_farmer_ids = fields.Many2many('res.partner', string='Farmers Responsible', compute='_compute_resposible_farmer_ids')
    
    def _compute_resposible_farmer_ids(self):
        for user in self:
            user.resposible_farmer_ids = user.cooperative_ids.farmer_group_ids.member_ids
    