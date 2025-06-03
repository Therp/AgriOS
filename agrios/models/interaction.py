# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FarmerInteraction(models.Model):
    _name = 'farmer.interaction'
    _description = 'Outgrower Interaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'interaction_date DESC'
    
    name = fields.Char('Summary', required=True, tracking=True)
    interaction_date = fields.Date('Date', required=True, tracking=True, index=True, default=fields.Date.today())
    outgrower_id = fields.Many2one('res.partner', 'Outgrower', domain=[('is_outgrower','=',True)], tracking=True, index=True)
    contract_id = fields.Many2one('farmer.contract', domain="[('outgrower_id','=',outgrower_id)]", tracking=True)
    interaction_type = fields.Selection([
        ('visit', 'Visit'),
        ('call', 'Call'),
        ('other', 'Other')
    ], 'Interaction Type', required=True, tracking=True)
    notes = fields.Text(required=True)
    active = fields.Boolean(default=True, tracking=True)
    
    @api.onchange('outgrower_id')
    def _onchange_outgrower_id(self):
        if self.contract_id and self.contract_id.outgrower_id != self.outgrower_id:
            self.contract_id = False
    