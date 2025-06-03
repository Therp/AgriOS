# -*- coding: utf-8 -*-

from odoo import fields, models, api, Command, _
from odoo.exceptions import ValidationError
from datetime import datetime


class ResPartnerSubplot(models.Model):
    _name = 'res.partner.subplot'
    _description = "Farmer Subplots"
    
    plot_id = fields.Many2one('farmer.plot', 'Plot', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Crop', domain=[('crop_product','=',True)], inverse="_update_farmer_harvest_products", required=True)
    acreage = fields.Float('Acreage', required=True)
    partner_id = fields.Many2one(related="plot_id.partner_id")
    plot_size = fields.Float(related="plot_id.plot_size", store=True)
    product_type = fields.Selection(related="product_id.harvest_product_type", store=True)
    number_of_trees = fields.Integer('Number of Trees')
    year_of_plantation = fields.Integer('Year of Plantation')
    age = fields.Integer('Age', compute='_compute_age')
    annual_estimated_yield = fields.Float('Annual Estimated Yield (KG)', compute='_compute_annual_estimated_yield')
    
    @api.depends('year_of_plantation')
    def _compute_age(self):
        current_year = datetime.now().year
        for record in self:
            if record.year_of_plantation:
                record.age = max(0, current_year - record.year_of_plantation)
            else:
                record.age = 0
    
    def get_crop_yield_estimate(self, duration=0):
        self.ensure_one()
        annual_estimated_yield = 0
        if self.product_type == 'tree_crop':
            tree_yield = self.env['plant.age.yield'].search([
                ('crop_product_id', '=', self.product_id.id),
                ('age', '<=', self.age + duration)
            ], order='age desc', limit=1)
            
            if tree_yield:
                annual_estimated_yield = tree_yield.annual_yield * self.number_of_trees
        elif self.product_type == 'perennial':
            annual_estimated_yield = self.product_id.estimated_yield * self.acreage
        else:
            annual_estimated_yield = 0
        return annual_estimated_yield
        
    @api.depends('product_id', 'product_type', 'year_of_plantation', 'number_of_trees', 'acreage')
    def _compute_annual_estimated_yield(self):
        for record in self:
            record.annual_estimated_yield = record.get_crop_yield_estimate(duration=0)
    
    @api.constrains('acreage', 'plot_size')
    def _validate_acreage(self):
        for record in self:
            if record.acreage > record.plot_size:
                raise ValidationError(_("The acreage of the subplot cannot be greater than the acreage of the linked plot."))
    
    @api.constrains('product_type', 'number_of_trees', 'year_of_plantation')
    def _validate_tree_crop_data(self):
        current_year = datetime.now().year
        for record in self:
            if record.product_type == 'tree_crop':
                if not record.number_of_trees or not record.year_of_plantation:
                    raise ValidationError(_(f"For tree crops in plot {record.plot_id.name}, both the 'Number of Trees' and 'Year of Plantation' must be provided."))
                if record.year_of_plantation < 1800:
                    raise ValidationError(_(f"Error in plot {record.plot_id.name}. Year of Plantation cannot be less than 1800."))
                if record.year_of_plantation > current_year:
                    raise ValidationError(_(f"Error in plot {record.plot_id.name}. Year of Plantation cannot be in the future."))
    
    def _update_farmer_harvest_products(self):
        for record in self:
            if record.product_id not in record.partner_id.crop_product_ids:
                record.partner_id.write({
                    'crop_product_ids': [Command.link(record.product_id.id)]
                })
    