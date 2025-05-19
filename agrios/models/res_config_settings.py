# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    @api.model
    def _get_farm_uom_domain(self):
        return [('category_id.id','=',self.env.ref('uom.uom_categ_surface').id), ('uom_type','=','bigger')]
        
    group_offtake_agreement = fields.Boolean("Offtake Agreements Contracts", implied_group='agrios.group_offtake_agreement')
    group_farmers_training = fields.Boolean("Farmers Training", implied_group='agrios.group_farmers_training')
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
    
    farm_uom = fields.Many2one('uom.uom', string='Unit of Measure', config_parameter='outgrower_management.farm_uom', domain=lambda self: self._get_farm_uom_domain(), default=lambda self: self.env.ref('agrios.area_1', raise_if_not_found=False))
    max_land_size = fields.Float(config_parameter='outgrower_management.max_land_size')
    
    @api.onchange('group_offtake_agreement')
    def _onchange_group_offtake_agreement(self):
        if not self.group_offtake_agreement:
            self.agrios_default_contract_needed = False
    
    @api.constrains('farm_uom')
    def _check_farm_uom(self):
        for record in self:
            if record.farm_uom.id == (int(self.env['ir.config_parameter'].sudo().get_param('outgrower_management.farm_uom') or 0) or self.env.ref('agrios.area_1').id):
                continue
            
            outgrowers_count = self.env['res.partner'].search_count([('is_outgrower','=',True)])
            if outgrowers_count > 0:
                raise ValidationError(_("You cannot change the UoM once an outgrower has been registered."))
    