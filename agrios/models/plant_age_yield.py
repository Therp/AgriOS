# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PlantAgeYield(models.Model):
    _name = 'plant.age.yield'
    _description = 'Projected Plant Age Yields'
    _order = 'product_id, age'
    
    product_id = fields.Many2one('product.template', string='Crop', domain=[('harvest_product', '=', True),('harvest_product_type','=','tree_crop')], required=True, ondelete='cascade', index=True)
    age = fields.Integer('Age From', required=True, help="The age from when the product will have the set yield")
    annual_yield = fields.Float('Annual Yield per Tree (KG)', required=True, digits=(10, 2))
    
    _sql_constraints = [
        ('unique_product_age', 'UNIQUE(product_id, age)', 'A yield record for this crop and age already exists.'),
        ('positive_age', 'CHECK(age >= 0)', 'The age cannot be a negative number.'),
        ('positive_yield', 'CHECK(annual_yield >= 0)', 'The annual yield cannot be a negative number.')
    ]
    