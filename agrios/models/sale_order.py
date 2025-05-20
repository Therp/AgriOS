# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    verified_partner_outgrower = fields.Boolean(compute='_compute_verified_partner_outgrower')
    outgrower_requires_contract = fields.Boolean(related='partner_id.outgrower_requires_contract', readonly=True)
    partner_open_contract_ids = fields.One2many(related='partner_id.open_contract_ids', readonly=True)
    partner_open_contract_input_ids = fields.One2many(related='partner_id.open_contract_input_ids', readonly=True)
    agrios_oa_id = fields.Many2one('offtake.agreement', 'AgriOS Contract', domain="[('outgrower_id','=',partner_id),('contract_stage','=','open'),('company_id','=',company_id)]")
    payment_in_kind = fields.Boolean('Payment In Kind', tracking=True)
    
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
                contracts = self.partner_open_contract_input_ids
            
            if len(contracts) == 1:
                self.agrios_oa_id = contracts
            else:
                self.agrios_oa_id = False
        else:
            self.agrios_oa_id = False
    
    def _onchange_company_id_warning(self):
        if not self._context.get('avoid_onchange_company_warning'):
            return super()._onchange_company_id_warning()
    
    @api.onchange('agrios_oa_id')
    def _onchange_agrios_oa_id(self):
        if self.agrios_oa_id:
            self.currency_id = self.agrios_oa_id.currency_id
            
            order_line_vals = [(5,0,0)]
            input_products = self.env['product.product']
            
            seed_prd = self.agrios_oa_id.seed_variety_id
            if seed_prd:
                input_products |= seed_prd
                input_products |= seed_prd.related_inputs_ids
            input_products |= self.agrios_oa_id.contracted_crop_id.related_inputs_ids
            
            for input_prd in input_products:
                vals = {
                    'product_id': input_prd.id,
                    'product_uom_qty': (self.agrios_oa_id.contracted_farm_acreage * input_prd.qty_per_acreage) or 1.0,
                }
                order_line_vals.append((0, 0, vals))
            
            self.order_line = order_line_vals
    
    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        
        if self.payment_in_kind:
            payment_in_kind_journals = self.env['account.journal'].search([('payment_in_kind','=',True),('type','=','sale'),('company_id','=',self.company_id.id)], order='id ASC', limit=1)
            if not payment_in_kind_journals:
                raise ValidationError(_("No journals defined as a 'payment in kind' journal"))
            
            values.update({
                'payment_in_kind': True,
                'journal_id': payment_in_kind_journals.id,
            })
        
        return values
    

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    agrios_oa_line_id = fields.Many2one(related='order_id.agrios_oa_id')
    date_order = fields.Datetime(related='order_id.date_order', string="Order Date/Time", store=True, index=True)
    coop_id = fields.Many2one(related='order_partner_id.coop_id', store=True)
    district_id = fields.Many2one(related='order_partner_id.coop_id.district_id', store=True)
    area_level_3_id = fields.Many2one(related='order_partner_id.coop_id.district_id.area_level_3_id', store=True)
    farmer_group_id = fields.Many2one(related='order_partner_id.farmer_group_id', store=True)
    
    @api.onchange('product_template_id')
    def _onchange_agrios_order(self):
        for order in self:
            if order.agrios_oa_line_id:
                order.product_uom_qty = max(order.product_template_id.qty_per_acreage * order.agrios_oa_line_id.contracted_farm_acreage, 1)
    