# -*- coding: utf-8 -*-

from odoo import models, fields


class FarmerGroup(models.Model):
    _inherit = 'farmer.group'
    
    coop_idx = fields.Integer(related='coop_id.id', string='Coop/Cluster ID')
    

class Farmer(models.Model):
    _inherit = 'res.partner'
    
    farmer_group_idx = fields.Integer(related='farmer_group_id.id', string='Farmers Group ID')
    coop_idx = fields.Integer(related='coop_id.id', string='Coop/Cluster ID')
    

class Cooperative(models.Model):
    _inherit = 'cooperative'
    
    district_idx = fields.Integer(related='district_id.id', string='District ID')
    region_idx = fields.Integer(related='district_id.region_id.id', string='Region ID')
    

class District(models.Model):
    _inherit = 'district'
    
    region_idx = fields.Integer(related='region_id.id', string='Region ID')
    