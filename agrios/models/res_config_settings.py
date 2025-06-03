# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    @api.model
    def _get_land_area_uom_domain(self):
        return [('category_id.id','=',self.env.ref('uom.uom_categ_surface').id), ('uom_type','=','bigger')]
        
    group_farmer_contract = fields.Boolean("Farmer Contracts", implied_group='agrios.group_farmer_contract')
    group_farmers_training = fields.Boolean("Farmer Trainings", implied_group='agrios.group_farmers_training')
    group_farmers_interactions = fields.Boolean("Farmer Interactions", implied_group='agrios.group_farmers_interactions')
    group_farmers_certifications = fields.Boolean("Farmer Certifications", implied_group='agrios.group_farmers_certifications')
    group_seed_varieties = fields.Boolean("Seed Varieties", implied_group='agrios.group_seed_varieties')
    group_plot_management = fields.Boolean("Plot Management", implied_group='agrios.group_plot_management')
    group_payments_in_kind = fields.Boolean("Payments In Kind", implied_group='agrios.group_payments_in_kind')
    group_plot_maps = fields.Boolean("Plot On Maps", implied_group='agrios.group_plot_maps')
    
    agrios_default_contract_needed = fields.Boolean(related='company_id.agrios_default_contract_needed', string="Default Contract Required", readonly=False)
    agrios_close_expired_contracts = fields.Boolean(related='company_id.agrios_close_expired_contracts', string="Automatically Close Expired Contracts", readonly=False)
    agrios_allow_operations_out_of_phase = fields.Boolean(related='company_id.agrios_allow_operations_out_of_phase', string="Allow Operations Out Of Phase", readonly=False)
    agrios_payment_in_kind_optional = fields.Boolean(related='company_id.agrios_payment_in_kind_optional', string="Payments In Kind Optional Reconciliation", readonly=False)
    
    land_area_uom = fields.Many2one('uom.uom', string='Land Area Unit of Measure', config_parameter='farmer_management.land_area_uom', domain=lambda self: self._get_land_area_uom_domain(), default=lambda self: self.env.ref('agrios.area_1', raise_if_not_found=False))
    max_plot_size = fields.Float(config_parameter='farmer_management.max_plot_size')
    
    @api.onchange('group_farmer_contract')
    def _onchange_group_farmer_contract(self):
        if not self.group_farmer_contract:
            self.agrios_default_contract_needed = False
    
    @api.constrains('land_area_uom')
    def _check_land_area_uom(self):
        for record in self:
            if record.land_area_uom.id == (int(self.env['ir.config_parameter'].sudo().get_param('farmer_management.land_area_uom') or 0) or self.env.ref('agrios.area_1').id):
                continue
            
            farmers_count = self.env['res.partner'].search_count([('is_farmer','=',True)])
            if farmers_count > 0:
                raise ValidationError(_("You cannot change the UoM once an farmer has been registered."))
    