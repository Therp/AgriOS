# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FarmerContract(models.Model):
    _name = 'farmer.contract'
    _description = 'Farmer Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['name', 'farmer_id']
    
    name = fields.Char('Contract Reference', default='/', readonly=True, copy=False)
    
    farmer_id = fields.Many2one('res.partner', domain=[('is_farmer','=',True),('farmer_stage','=','verified')], required=True, tracking=True)
    farmer_id_number = fields.Char('ID Number', related='farmer_id.farmer_id_number')
    
    season_id = fields.Many2one('season', required=True, tracking=True)
    season_start_date = fields.Date('Start Date', related='season_id.start_date')
    season_end_date = fields.Date('End date', related='season_id.end_date')
    
    contract_stage = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')],
        default='draft', string='Contract Stage', copy=False)
    
    contracted_crop_id = fields.Many2one('product.product', required=True, domain="[('id','in',farmer_crop_product_ids)]")
    
    available_seed_ids = fields.One2many(related='contracted_crop_id.seed_ids', readonly=True)
    seed_variety_id = fields.Many2one('product.product', 'Seed Variety')
    
    land_area_uom = fields.Many2one(related='farmer_id.land_area_uom')
    contract_acreage = fields.Float('Contracted Acreage', tracking=True)
    
    total_acreage = fields.Float('Total Plot Acreage', related='farmer_id.total_acreage')
    total_contracted_acreage = fields.Float('Total Contracted Acreage', related='farmer_id.total_contracted_acreage')
    non_contracted_acreage = fields.Float('Non-Contracted Acreage', related='farmer_id.non_contracted_acreage')
    
    contracted_offtake_qty = fields.Integer('Contracted Offtake Qty', tracking=True)
    received_offtake_qty = fields.Integer('Received Qty', compute='_compute_received_offtake_qty')
    offtake_available_qty = fields.Integer('Pending Offtake Qty', compute='_compute_offtake_available_qty')
    
    contracted_unit_price = fields.Monetary()
    total_contract_cost = fields.Monetary('Total Contract Cost', compute='_compute_total_offtake_cost')
    total_inputs_cost = fields.Monetary('Total Inputs Cost', compute='_compute_total_inputs_cost')
    
    oa_input_ids = fields.One2many('sale.order.line', 'farmer_contract_line_id', domain=[('state','not in',['draft','sent','cancel'])])
    count_oa_input_sales = fields.Integer(compute='_compute_count_oa_input_sales')
    
    count_oa_purchases = fields.Integer(compute='_compute_count_oa_purchases')
    farmer_contract_offtake_ids = fields.One2many('purchase.order.line', 'farmer_contract_line_id',string="Farmer Contract Offtakes", domain=[('state','not in',['draft','sent','to approve','cancel'])])
    
    interaction_ids = fields.One2many('farmer.interaction', 'contract_id')
    ready_for_harvest = fields.Boolean('Ready For Harvest', default=False, copy=False)
    harvest_state = fields.Selection([('input', 'Input Stage'),('harvest', 'Harvest Stage')], 'Input/Harvest Stage', compute='_compute_harvest_state', store=True)
    
    balance_qty = fields.Integer(compute='_compute_balance_qty')
    same_unutilized_contracted = fields.Boolean(compute='_compute_same_unutilized_contracted', help='If the contracted area is the same as the unutilized area')
    
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    active_contract = fields.Boolean('Active Contract', compute='_compute_active_contract')
    expired_contract = fields.Boolean('Contract Expired', compute='_compute_expired_contract', search='_search_expired_contract')
    
    has_offtake_order = fields.Boolean('Has Offtake Order', compute='_compute_has_offtake_order', search='_search_has_offtake_order')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    
    active = fields.Boolean('Active (Legacy)', default=True, readonly=True)
    
    can_order_inputs = fields.Boolean(compute='_compute_can_order_inputs')
    can_register_offtakes = fields.Boolean(compute='_compute_can_register_offtakes')
    
    farmer_crop_product_ids = fields.Many2many(related='farmer_id.crop_product_ids', string='Crop Products')
    
    @api.depends('ready_for_harvest', 'contract_stage')
    def _compute_harvest_state(self):
        for contract in self:
            if contract.contract_stage == 'open':
                contract.harvest_state = contract.ready_for_harvest and 'harvest' or 'input'
            else:
                contract.harvest_state = False
    
    @api.depends('contract_stage', 'ready_for_harvest')
    def _compute_can_order_inputs(self):
        for contract in self:
            contract.can_order_inputs = bool(contract.contract_stage == 'open' and (not contract.ready_for_harvest or contract.company_id.allow_operations_out_of_phase))
    
    @api.depends('contract_stage', 'ready_for_harvest')
    def _compute_can_register_offtakes(self):
        for contract in self:
            contract.can_register_offtakes = bool(contract.contract_stage == 'open' and (contract.ready_for_harvest or contract.company_id.allow_operations_out_of_phase))
    
    def _compute_has_offtake_order(self):
        for contract in self:
            contract.has_offtake_order = bool(contract.farmer_contract_offtake_ids.filtered(lambda pol: pol.state != 'cancel'))
    
    @api.depends('contract_stage', 'contracted_offtake_qty', 'received_offtake_qty')
    def _compute_offtake_available_qty(self):
        for contract in self:
            if contract.contract_stage == 'open':
                contract.offtake_available_qty = contract.contracted_offtake_qty - contract.received_offtake_qty
            else:
                contract.offtake_available_qty = 0
    
    @api.depends('contract_stage', 'season_start_date', 'season_end_date')
    def _compute_active_contract(self):
        today = fields.Date.today()
        for contract in self:
            if contract.contract_stage != 'open' or today > contract.season_end_date or today < contract.season_start_date:
                contract.active_contract = False
            else:
                contract.active_contract = True
    
    @api.depends('contract_stage', 'season_start_date', 'season_end_date')
    def _compute_expired_contract(self):
        today = fields.Date.today()
        for contract in self:
            if contract.contract_stage == 'open' and today > contract.season_end_date:
                contract.expired_contract = True
            else:
                contract.expired_contract = False
        
    @api.depends('received_offtake_qty', 'contracted_offtake_qty')
    def _compute_balance_qty(self):
        for rec in self:
            rec.balance_qty = rec.received_offtake_qty - rec.contracted_offtake_qty
    
    @api.depends('non_contracted_acreage', 'contract_acreage')
    def _compute_same_unutilized_contracted(self):
        for offtake_contract in self:
            offtake_contract.same_unutilized_contracted = offtake_contract.non_contracted_acreage == offtake_contract.contract_acreage
    
    def _compute_count_oa_input_sales(self):
        for rec in self:
            rec.count_oa_input_sales = self.env['sale.order'].search_count([('farmer_contract_id', '=', rec.id)])
    
    def _compute_count_oa_purchases(self):
        for rec in self:
            rec.count_oa_purchases = self.env['purchase.order'].search_count([('farmer_contract_id', '=', rec.id)])
    
    def _compute_total_inputs_cost(self):
        for rec in self:
            rec.total_inputs_cost = 0
            for line in rec.oa_input_ids:
                rec.total_inputs_cost += line.price_total
    
    @api.depends('contracted_offtake_qty', 'contracted_unit_price')
    def _compute_total_offtake_cost(self):
        for rec in self:
            rec.total_contract_cost = rec.contracted_offtake_qty * rec.contracted_unit_price
    
    @api.depends('name', 'farmer_id', 'season_id', 'contracted_crop_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.name != '/':
                rec.display_name = f"[{rec.name}] {rec.farmer_id.name} {rec.season_id.season} {rec.contracted_crop_id.name}"
            else:
                rec.display_name = f"{rec.farmer_id.name} {rec.season_id.season} {rec.contracted_crop_id.name}"
    
    def _compute_received_offtake_qty(self):
        for rec in self:
            rec.received_offtake_qty = 0
            for line in rec.farmer_contract_offtake_ids:
                rec.received_offtake_qty += line.qty_received
    
    def _search_expired_contract(self, operator, value):
        if (operator == '=' and not value) or (operator == '!=' and value):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        
        self._cr.execute("""
            SELECT cont.id
            FROM farmer_contract cont
            INNER JOIN season ON cont.season_id = season.id AND season.end_date < CURRENT_DATE
            WHERE cont.contract_stage = 'open'
            """)
        return [('id', domain_operator, [r[0] for r in self._cr.fetchall()])]
    
    def _search_has_offtake_order(self, operator, value):
        if (operator == '=' and not value) or (operator == '!=' and value):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        
        self._cr.execute("""
            SELECT DISTINCT cont.id
            FROM farmer_contract cont
            INNER JOIN purchase_order po ON po.farmer_contract_id = cont.id AND po.state != 'cancel'
            """)
        return [('id', domain_operator, [r[0] for r in self._cr.fetchall()])]
    
    # If a seed variety is set the estimated yield is set based on seed variety
    # If no seed variety is set the estimated yield is set based on the contracted crop
    @api.onchange('seed_variety_id', 'contract_acreage', 'contracted_crop_id')
    def _onchange_offtake_qty(self):
        for rec in self:
            if rec.contracted_crop_id and rec.contract_acreage:
                crop_product = rec.contracted_crop_id
                est_offtake = (
                    crop_product.estimated_yield if crop_product.harvest_product_type == 'perennial' 
                    else rec.farmer_id.get_offtake_estimate(crop_product)
                )
                rec.contracted_offtake_qty = est_offtake * rec.contract_acreage
            else:
                rec.contracted_offtake_qty = 0
    
    @api.onchange('contracted_crop_id')
    def _onchange_offtake_unit_price(self):
        for rec in self:
            rec.contracted_unit_price = rec.contracted_crop_id.standard_price    
    
    @api.onchange('contracted_crop_id')
    def _onchange_contracted_crop_id(self):
        if self.contracted_crop_id:
            if len(self.available_seed_ids) == 1:
                self.seed_variety_id = self.available_seed_ids
            elif self.seed_variety_id and self.seed_variety_id.crop_product_id != self.contracted_crop_id:
                self.seed_variety_id = False
        else:
            self.seed_variety_id = False
    
    @api.onchange('seed_variety_id')
    def _onchange_seed_variety_id(self):
        if not self.contracted_crop_id and self.seed_variety_id.crop_product_id:
            self.contracted_crop_id = self.seed_variety_id.crop_product_id
    
    @api.onchange('farmer_id')
    def _onchange_farmer_id(self):
        if self.farmer_id:
            self.contract_acreage = self.farmer_id.non_contracted_acreage
            
            if self.contracted_crop_id and self.contracted_crop_id not in self.farmer_crop_product_ids:
                self.contracted_crop_id = False
            
            if not self.contracted_crop_id and len(self.farmer_crop_product_ids) == 1:
                self.contracted_crop_id = self.farmer_crop_product_ids
    
    def unlink(self):
        for contract in self:
            if contract.name != '/':
                raise UserError(_("You can't delete a contract with a reference generated! Cancel the contract instead."))
        return super().unlink()
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('verify_agrios_purchase'):
            company_id = self._context['verify_agrios_purchase']
            company = self.env.company if self.env.company.id == company_id else self.env['res.company'].browse(company_id)
            
            if not company.allow_operations_out_of_phase:
                if not args: args = []
                args = [('ready_for_harvest','=',True)] + args
        
        elif self._context.get('verify_agrios_sale'):
            company_id = self._context['verify_agrios_sale']
            company = self.env.company if self.env.company.id == company_id else self.env['res.company'].browse(company_id)
            
            if not company.allow_operations_out_of_phase:
                if not args: args = []
                args = [('ready_for_harvest','=',False)] + args
        
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
    
    def btn_set_contracted_mapped_qty(self):
        for offtake_contract in self:
            if offtake_contract.contract_stage != 'draft':
                raise UserError(_('The contracted area can only be changed when the contract is in draft status.'))
            offtake_contract.contract_acreage = offtake_contract.non_contracted_acreage
            offtake_contract._onchange_offtake_qty()
    
    def btn_cancel_contract(self):
        self.cancel_farmer_contract()
    
    def action_create_agrios_oa_sale_orders(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Order Inputs'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': {
                'default_partner_id': self.farmer_id.id,
                'default_agrios_oa_id': self.id,
                'default_company_id': self.company_id.id,
            }
        }
    
    def action_agrios_oa_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Order Inputs'),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('farmer_contract_id', '=', self.id)],
            'help': '<p class="o_view_nocontent_smiling_face">Contract without any order inputs</p>',
            'context': {
                'create': False,
            }
        }
    
    def action_create_agrios_oa_purchase_order(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Off-Take'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': {
                'default_partner_id': self.farmer_id.id,
                'default_agrios_oa_id': self.id,
                'default_origin': self.name,
                'default_company_id': self.company_id.id,
            }
        }
    
    def action_agrios_oa_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Off-Takes'),
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('farmer_contract_id','=',self.id)],
            'help': '<p class="o_view_nocontent_smiling_face">Contract without any off-takes</p>',
            'context': {
                'create': False,
            }
        }
    
    def confirm_farmer_contract(self):
        farm_area_cache = {}
        for offtake_contract in self:  # first do the validation loop not to create gaps in the sequence in case some case fails
            if offtake_contract.contracted_offtake_qty <= 0.0:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Offtake quantity must be greater than zero"))
            
            if offtake_contract.contract_acreage <= 0.0:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Contracted acreage must be greater than zero"))
            
            if offtake_contract.farmer_id.id not in farm_area_cache:
                farm_area_cache[offtake_contract.farmer_id.id] = offtake_contract.non_contracted_acreage
            
            if offtake_contract.contract_acreage > farm_area_cache[offtake_contract.farmer_id.id]:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Contracted acreage cannot be higher than the current unutilized farm value. If more acreage is to be contractualized for this farmer, the plots need to be mapped first, and added to the system"))
            
            farm_area_cache[offtake_contract.farmer_id.id] -= offtake_contract.contract_acreage
            
        for offtake_contract in self:
            vals = {'contract_stage': 'open'}
            
            if offtake_contract.name == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('farmer.contract')
            
            offtake_contract.write(vals)
        
            offtake_contract.message_post(body=_('Contract confirmed.'))
    
    def close_farmer_contract(self):
        self.write({'contract_stage': 'closed'})
        for contract in self:
            contract.message_post(body=_('Contract closed.'))
    
    def cancel_farmer_contract(self):
        for contract in self:
            if contract.oa_input_ids or contract.farmer_contract_offtake_ids:
                raise UserError(_(f"Contract {contract.display_name} Warning - You can't cancel a contract with input orders or off-take order. Either cancel those orders or close the contract."))
        
        self.write({'contract_stage': 'cancelled'})
        
        for contract in self:
            contract.message_post(body=_('Contract cancelled.'))
    
    def set_ready_for_harvest(self):
        self.write({'ready_for_harvest': True})
        for contract in self:
            contract.message_post(body=_('Contract set ready for harvest.'))
    
    def _cron_close_expired_contracts(self):
        for company in self.env['res.company'].sudo().search([('close_expired_contracts','=',True)]):
            expired_contracts = self.sudo().search([('company_id','=',company.id),('expired_contract','=',True)])
            if expired_contracts:
                expired_contracts.close_farmer_contract()
    