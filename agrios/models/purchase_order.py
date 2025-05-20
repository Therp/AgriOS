# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    verified_partner_outgrower = fields.Boolean(compute='_compute_verified_partner_outgrower')
    outgrower_requires_contract = fields.Boolean(related='partner_id.outgrower_requires_contract', readonly=True)
    partner_open_contract_ids = fields.One2many(related='partner_id.open_contract_ids', readonly=True)
    partner_open_contract_harvest_ids = fields.One2many(related='partner_id.open_contract_harvest_ids', readonly=True)
    agrios_oa_id = fields.Many2one('offtake.agreement', 'AgriOS Contract', domain="[('outgrower_id','=',partner_id),('contract_stage','=','open'),('company_id','=',company_id)]")
    
    @api.depends('partner_id')
    def _compute_verified_partner_outgrower(self):
        for so in self:
            so.verified_partner_outgrower = (so.partner_id.is_outgrower and so.partner_id.outgrower_stage == 'verified')
    
    @api.onchange('partner_id')
    def _onchange_agrios_contract(self):
        if self.partner_id:
            if self.agrios_oa_id and self.agrios_oa_id.outgrower_id == self.partner_id:
                return
            
            company = self.company_id or self.env.company
            
            if company.agrios_allow_operations_out_of_phase:
                contracts = self.partner_open_contract_ids
            else:
                contracts = self.partner_open_contract_harvest_ids
            
            if len(contracts) == 1:
                self.agrios_oa_id = contracts
            else:
                self.agrios_oa_id = False
        else:
            self.agrios_oa_id = False
    
    @api.onchange('agrios_oa_id')
    def _onchange_agrios_oa_id(self):
        if self.agrios_oa_id:
            oftake_prd = self.agrios_oa_id.contracted_crop_id
            balance_qty = max(self.agrios_oa_id.balance_qty * -1, 0)
            
            self.order_line = [(5,0,0), (0,0,{
                'product_id': oftake_prd.id,
                'name': oftake_prd.display_name,
                'product_qty': balance_qty,
                'product_uom': oftake_prd.uom_po_id.id,
            })]
            self.currency_id = self.agrios_oa_id.currency_id
    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    agrios_oa_line_id = fields.Many2one('offtake.agreement', related='order_id.agrios_oa_id')
    date_order = fields.Datetime(store=True, index=True)
    coop_id = fields.Many2one(related='partner_id.coop_id', store=True)
    district_id = fields.Many2one(related='partner_id.coop_id.district_id', store=True)
    area_level_3_id = fields.Many2one(related='partner_id.coop_id.district_id.area_level_3_id', store=True)
    farmer_group_id = fields.Many2one(related='partner_id.farmer_group_id', store=True)
    
    def _compute_price_unit_and_date_planned_and_name(self):
        ret = super()._compute_price_unit_and_date_planned_and_name()
        
        if self.order_id.agrios_oa_id and self.product_id and self.product_id == self.order_id.agrios_oa_id.contracted_crop_id:
            self.price_unit = self.order_id.agrios_oa_id.offtake_unit_price
        
        return ret
    