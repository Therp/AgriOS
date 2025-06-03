# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    verified_partner_farmer = fields.Boolean(compute='_compute_verified_partner_farmer', string='Verified Partner Farmer')
    farmer_requires_contract = fields.Boolean(related='partner_id.farmer_requires_contract', readonly=True, string='Requires Contract')
    partner_open_contract_ids = fields.One2many(related='partner_id.open_contract_ids', readonly=True)
    partner_open_contract_input_ids = fields.One2many(related='partner_id.open_contract_input_ids', readonly=True)
    farmer_contract_id = fields.Many2one('farmer.contract', 'Farmer Contract', domain="[('farmer_id','=',partner_id),('contract_stage','=','open'),('company_id','=',company_id)]")
    payment_in_kind = fields.Boolean('Payment In Kind', tracking=True)
    
    @api.depends('partner_id')
    def _compute_verified_partner_farmer(self):
        for so in self:
            so.verified_partner_farmer = (so.partner_id.is_farmer and so.partner_id.farmer_stage == 'verified')
    
    @api.onchange('partner_id')
    def _onchange_agrios_contract(self):
        if self.partner_id:
            if self.farmer_contract_id and self.farmer_contract_id.farmer_id == self.partner_id:
                return
            
            company = self.company_id or self.env.company
            
            if company.allow_operations_out_of_phase:
                contracts = self.partner_open_contract_ids
            else:
                contracts = self.partner_open_contract_input_ids
            
            if len(contracts) == 1:
                self.farmer_contract_id = contracts
            else:
                self.farmer_contract_id = False
        else:
            self.farmer_contract_id = False
    
    def _onchange_company_id_warning(self):
        if not self._context.get('avoid_onchange_company_warning'):
            return super()._onchange_company_id_warning()
    
    @api.onchange('farmer_contract_id')
    def _onchange_agrios_oa_id(self):
        if self.farmer_contract_id:
            self.currency_id = self.farmer_contract_id.currency_id
            
            order_line_vals = [(5,0,0)]
            input_products = self.env['product.product']
            
            seed_prd = self.farmer_contract_id.seed_variety_id
            if seed_prd:
                input_products |= seed_prd
                input_products |= seed_prd.related_inputs_ids
            input_products |= self.farmer_contract_id.contracted_crop_id.related_inputs_ids
            
            for input_prd in input_products:
                vals = {
                    'product_id': input_prd.id,
                    'product_uom_qty': (self.farmer_contract_id.contract_acreage * input_prd.qty_per_acreage) or 1.0,
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
    
    farmer_contract_line_id = fields.Many2one(related='order_id.farmer_contract_id')
    date_order = fields.Datetime(related='order_id.date_order', string="Order Date/Time", store=True, index=True)
    loc_area_1_id = fields.Many2one(related='order_partner_id.loc_area_1_id', store=True)
    loc_area_2_id = fields.Many2one(related='order_partner_id.loc_area_2_id', store=True)
    loc_area_3_id = fields.Many2one(related='order_partner_id.loc_area_3_id', store=True)
    loc_area_4_id = fields.Many2one(related='order_partner_id.loc_area_4_id', store=True)
    loc_area_5_id = fields.Many2one(related='order_partner_id.loc_area_5_id', store=True)
    loc_area_6_id = fields.Many2one(related='order_partner_id.loc_area_6_id', store=True)
    country_id = fields.Many2one(related='loc_area_1_id.country_id', store=True)
    farmer_group_id = fields.Many2one(related='order_partner_id.farmer_group_id', store=True)
    
    @api.onchange('product_template_id')
    def _onchange_agrios_order(self):
        for order in self:
            if order.farmer_contract_line_id:
                order.product_uom_qty = max(order.product_template_id.qty_per_acreage * order.farmer_contract_line_id.contract_acreage, 1)
    