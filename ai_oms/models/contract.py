# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OfftakeAgreementContract(models.Model):
    _name = 'offtake.agreement'
    _description = 'Offtake Agreement Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['name', 'outgrower_id']
    
    name = fields.Char('Contract Reference', default='/', readonly=True, copy=False)
    
    outgrower_id = fields.Many2one('res.partner', domain=[('is_outgrower','=',True),('outgrower_stage','=','verified')], required=True, tracking=True)
    og_doc_id = fields.Char('National ID', related='outgrower_id.outgrower_identification')
    
    season_id = fields.Many2one('season', required=True, tracking=True)
    season_start_date = fields.Date('Start Date', related='season_id.start_date')
    season_end_date = fields.Date('End date', related='season_id.end_date')
    
    contract_stage = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')],
        default='draft', string='Contract Stage', copy=False)
    
    contracted_crop_id = fields.Many2one('product.product', required=True, domain="[('id','in',farmer_harvest_crop_ids)]")
    
    available_seed_ids = fields.One2many(related='contracted_crop_id.seed_ids', readonly=True)
    seed_variety_id = fields.Many2one('product.product', 'Seed Variety')
    
    farm_uom = fields.Many2one(related='outgrower_id.farm_uom')
    contracted_farm_acreage = fields.Float('Contracted Farm', tracking=True)
    
    total_farm_acreage = fields.Float('Total Farm', related='outgrower_id.total_land_size')
    utilized_acreage = fields.Float('Utilized Farm', related='outgrower_id.utilized_acreage')
    unutilized_acreage = fields.Float('Unutilized Farm', related='outgrower_id.unutilized_acreage')
    
    offtake_qty = fields.Integer(tracking=True)
    received_offtake_qty = fields.Integer('Received Qty', compute='_compute_received_offtake_qty')
    offtake_available_qty = fields.Integer('Pending Off-Take Qty', compute='_compute_offtake_available_qty')
    
    offtake_unit_price = fields.Monetary()
    total_offtake_cost = fields.Monetary('Total Offtake Cost', compute='_compute_total_offtake_cost')
    farm_inputs_cost = fields.Monetary('Total Farm Loan', compute='_compute_farm_inputs_cost')
    
    oa_input_ids = fields.One2many('sale.order.line', 'oms_oa_line_id', domain=[('state','not in',['draft','sent','cancel'])])
    count_oa_input_sales = fields.Integer(compute='_compute_count_oa_input_sales')
    
    count_oa_purchases = fields.Integer(compute='_compute_count_oa_purchases')
    oa_offtake_ids = fields.One2many('purchase.order.line', 'oms_oa_line_id', domain=[('state','not in',['draft','sent','to approve','cancel'])])
    
    interaction_ids = fields.One2many('farmer.interaction', 'contract_id')
    ready_for_harvest = fields.Boolean('Ready For Harvest', default=False, copy=False)
    harvest_state = fields.Selection([('input', 'Input Stage'),('harvest', 'Harvest Stage')], 'Input/Harvest Stage', compute='_compute_harvest_state', store=True)
    
    balance_qty = fields.Integer(compute='_compute_balance_qty')
    same_unutilized_contracted = fields.Boolean(compute='_compute_same_unutilized_contracted', help='If the contracted area is the same as the unutilized area')
    
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    active_contract = fields.Boolean('Active Contract', compute='_compute_active_contract')
    expired_contract = fields.Boolean('Contract Expired', compute='_compute_expired_contract', search='_search_expired_contract')
    
    has_offtake_order = fields.Boolean('Has Off-Take Order', compute='_compute_has_offtake_order', search='_search_has_offtake_order')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    
    active = fields.Boolean('Active (Legacy)', default=True, readonly=True)
    
    can_order_inputs = fields.Boolean(compute='_compute_can_order_inputs')
    can_regist_offtakes = fields.Boolean(compute='_compute_can_regist_offtakes')
    
    farmer_harvest_crop_ids = fields.Many2many(related='outgrower_id.harvest_crop_ids')
    
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
            contract.can_order_inputs = bool(contract.contract_stage == 'open' and (not contract.ready_for_harvest or contract.company_id.oms_allow_operations_out_of_phase))
    
    @api.depends('contract_stage', 'ready_for_harvest')
    def _compute_can_regist_offtakes(self):
        for contract in self:
            contract.can_regist_offtakes = bool(contract.contract_stage == 'open' and (contract.ready_for_harvest or contract.company_id.oms_allow_operations_out_of_phase))
    
    def _compute_has_offtake_order(self):
        for contract in self:
            contract.has_offtake_order = bool(contract.oa_offtake_ids.filtered(lambda pol: pol.state != 'cancel'))
    
    @api.depends('contract_stage', 'offtake_qty', 'received_offtake_qty')
    def _compute_offtake_available_qty(self):
        for contract in self:
            if contract.contract_stage == 'open':
                contract.offtake_available_qty = contract.offtake_qty - contract.received_offtake_qty
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
        
    @api.depends('received_offtake_qty', 'offtake_qty')
    def _compute_balance_qty(self):
        for rec in self:
            rec.balance_qty = rec.received_offtake_qty - rec.offtake_qty
    
    @api.depends('unutilized_acreage', 'contracted_farm_acreage')
    def _compute_same_unutilized_contracted(self):
        for offtake_contract in self:
            offtake_contract.same_unutilized_contracted = offtake_contract.unutilized_acreage == offtake_contract.contracted_farm_acreage
    
    def _compute_count_oa_input_sales(self):
        for rec in self:
            rec.count_oa_input_sales = self.env['sale.order'].search_count([('oms_oa_id', '=', rec.id)])
    
    def _compute_count_oa_purchases(self):
        for rec in self:
            rec.count_oa_purchases = self.env['purchase.order'].search_count([('oms_oa_id', '=', rec.id)])
    
    def _compute_farm_inputs_cost(self):
        for rec in self:
            rec.farm_inputs_cost = 0
            for line in rec.oa_input_ids:
                rec.farm_inputs_cost += line.price_total
    
    @api.depends('offtake_qty', 'offtake_unit_price')
    def _compute_total_offtake_cost(self):
        for rec in self:
            rec.total_offtake_cost = rec.offtake_qty * rec.offtake_unit_price
    
    @api.depends('name', 'outgrower_id', 'season_id', 'contracted_crop_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.name != '/':
                rec.display_name = f"[{rec.name}] {rec.outgrower_id.name} {rec.season_id.season} {rec.contracted_crop_id.name}"
            else:
                rec.display_name = f"{rec.outgrower_id.name} {rec.season_id.season} {rec.contracted_crop_id.name}"
    
    def _compute_received_offtake_qty(self):
        for rec in self:
            rec.received_offtake_qty = 0
            for line in rec.oa_offtake_ids:
                rec.received_offtake_qty += line.qty_received
    
    def _search_expired_contract(self, operator, value):
        if (operator == '=' and not value) or (operator == '!=' and value):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        
        self._cr.execute("""
            SELECT cont.id
            FROM offtake_agreement cont
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
            FROM offtake_agreement cont
            INNER JOIN purchase_order po ON po.oms_oa_id = cont.id AND po.state != 'cancel'
            """)
        return [('id', domain_operator, [r[0] for r in self._cr.fetchall()])]
    
    # If a seed variety is set the estimated yield is set based on seed variety
    # If no seed variety is set the estimated yield is set based on the contracted crop
    @api.onchange('seed_variety_id', 'contracted_farm_acreage', 'contracted_crop_id')
    def _onchange_offtake_qty(self):
        for rec in self:
            if rec.contracted_crop_id and rec.contracted_farm_acreage:
                crop_product = rec.contracted_crop_id
                est_offtake = (
                    crop_product.est_yield if crop_product.harvest_product_type == 'perennial' 
                    else rec.outgrower_id.get_offtake_estimate(crop_product)
                )
                rec.offtake_qty = est_offtake * rec.contracted_farm_acreage
            else:
                rec.offtake_qty = 0
    
    @api.onchange('contracted_crop_id')
    def _onchange_offtake_unit_price(self):
        for rec in self:
            rec.offtake_unit_price = rec.contracted_crop_id.standard_price    
    
    @api.onchange('contracted_crop_id')
    def _onchange_contracted_crop_id(self):
        if self.contracted_crop_id:
            if len(self.available_seed_ids) == 1:
                self.seed_variety_id = self.available_seed_ids
            elif self.seed_variety_id and self.seed_variety_id.harvest_crop_id != self.contracted_crop_id:
                self.seed_variety_id = False
        else:
            self.seed_variety_id = False
    
    @api.onchange('seed_variety_id')
    def _onchange_seed_variety_id(self):
        if not self.contracted_crop_id and self.seed_variety_id.harvest_crop_id:
            self.contracted_crop_id = self.seed_variety_id.harvest_crop_id
    
    @api.onchange('outgrower_id')
    def _onchange_outgrower_id(self):
        if self.outgrower_id:
            self.contracted_farm_acreage = self.outgrower_id.unutilized_acreage
            
            if self.contracted_crop_id and self.contracted_crop_id not in self.farmer_harvest_crop_ids:
                self.contracted_crop_id = False
            
            if not self.contracted_crop_id and len(self.farmer_harvest_crop_ids) == 1:
                self.contracted_crop_id = self.farmer_harvest_crop_ids
    
    def unlink(self):
        for contract in self:
            if contract.name != '/':
                raise UserError(_("You can't delete a contract with a reference generated! Cancel the contract instead."))
        return super().unlink()
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('verify_oms_purchase'):
            company_id = self._context['verify_oms_purchase']
            company = self.env.company if self.env.company.id == company_id else self.env['res.company'].browse(company_id)
            
            if not company.oms_allow_operations_out_of_phase:
                if not args: args = []
                args = [('ready_for_harvest','=',True)] + args
        
        elif self._context.get('verify_oms_sale'):
            company_id = self._context['verify_oms_sale']
            company = self.env.company if self.env.company.id == company_id else self.env['res.company'].browse(company_id)
            
            if not company.oms_allow_operations_out_of_phase:
                if not args: args = []
                args = [('ready_for_harvest','=',False)] + args
        
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
    
    def btn_set_contracted_mapped_qty(self):
        for offtake_contract in self:
            if offtake_contract.contract_stage != 'draft':
                raise UserError(_('The contracted area can only be changed when the contract is in draft status.'))
            offtake_contract.contracted_farm_acreage = offtake_contract.unutilized_acreage
            offtake_contract._onchange_offtake_qty()
    
    def btn_cancel_contract(self):
        self.cancel_offtake_agreement()
    
    def action_create_oms_oa_sale_orders(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Order Inputs'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': {
                'default_partner_id': self.outgrower_id.id,
                'default_oms_oa_id': self.id,
                'default_company_id': self.company_id.id,
            }
        }
    
    def action_oms_oa_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Order Inputs'),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('oms_oa_id', '=', self.id)],
            'help': '<p class="o_view_nocontent_smiling_face">Contract without any order inputs</p>',
            'context': {
                'create': False,
            }
        }
    
    def action_create_oms_oa_purchase_order(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Off-Take'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': {
                'default_partner_id': self.outgrower_id.id,
                'default_oms_oa_id': self.id,
                'default_origin': self.name,
                'default_company_id': self.company_id.id,
            }
        }
    
    def action_oms_oa_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Off-Takes'),
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('oms_oa_id','=',self.id)],
            'help': '<p class="o_view_nocontent_smiling_face">Contract without any off-takes</p>',
            'context': {
                'create': False,
            }
        }
    
    def confirm_offtake_agreement(self):
        farm_area_cache = {}
        for offtake_contract in self:  # first do the validation loop not to create gaps in the sequence in case some case fails
            if offtake_contract.offtake_qty <= 0.0:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Offtake quantity must be greater than zero"))
            
            if offtake_contract.contracted_farm_acreage <= 0.0:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Contracted acreage must be greater than zero"))
            
            if offtake_contract.outgrower_id.id not in farm_area_cache:
                farm_area_cache[offtake_contract.outgrower_id.id] = offtake_contract.unutilized_acreage
            
            if offtake_contract.contracted_farm_acreage > farm_area_cache[offtake_contract.outgrower_id.id]:
                raise ValidationError(_(f"Contract {offtake_contract.display_name} Warning - Contracted acreage cannot be higher than the current unutilized farm value. If more acreage is to be contractualized for this farmer, the plots need to be mapped first, and added to the system"))
            
            farm_area_cache[offtake_contract.outgrower_id.id] -= offtake_contract.contracted_farm_acreage
            
        for offtake_contract in self:
            vals = {'contract_stage': 'open'}
            
            if offtake_contract.name == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('offtake.agreement')
            
            offtake_contract.write(vals)
        
            offtake_contract.message_post(body=_('Contract confirmed.'))
    
    def close_offtake_agreement(self):
        self.write({'contract_stage': 'closed'})
        for contract in self:
            contract.message_post(body=_('Contract closed.'))
    
    def cancel_offtake_agreement(self):
        for contract in self:
            if contract.oa_input_ids or contract.oa_offtake_ids:
                raise UserError(_(f"Contract {contract.display_name} Warning - You can't cancel a contract with input orders or off-take order. Either cancel those orders or close the contract."))
        
        self.write({'contract_stage': 'cancelled'})
        
        for contract in self:
            contract.message_post(body=_('Contract cancelled.'))
    
    def set_ready_for_harvest(self):
        self.write({'ready_for_harvest': True})
        for contract in self:
            contract.message_post(body=_('Contract set ready for harvest.'))
    
    def _cron_close_expired_contracts(self):
        for company in self.env['res.company'].sudo().search([('oms_close_expired_contracts','=',True)]):
            expired_contracts = self.sudo().search([('company_id','=',company.id),('expired_contract','=',True)])
            if expired_contracts:
                expired_contracts.close_offtake_agreement()
    