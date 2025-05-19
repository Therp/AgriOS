# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class BulkContractAbstractWizard(models.AbstractModel):
    _name = 'bulk.contract.abstract.wizard'
    _description = 'Bulk Contract Action Abstract Wizard'
    
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True, ondelete='cascade', default=lambda self: self.env.company)
    contract_ids = fields.Many2many('offtake.agreement', string='Contracts')
    show_expired_filter = fields.Boolean(default=True)
    view_contracts = fields.Boolean('View Contracts')
    
    region_ids = fields.Many2many('region', string='Regions')
    district_ids = fields.Many2many('district', string='District')
    cooperative_ids = fields.Many2many('cooperative', string='Communities')
    farmer_group_ids = fields.Many2many('farmer.group', string='Farmer Groups')
    
    season_id = fields.Many2one('season', 'Season', domain=[('status','in',('open','lock'))])
    product_id = fields.Many2one('product.product', 'Harvestable Product', domain=[('harvest_product','=',True)])
    expired_filter = fields.Selection([('expired','Expired Only'),('not_expired','Not Expired Only')], 'Expired Contracts')
    
    @api.onchange('region_ids')
    def _onchange_region_ids(self):
        self.district_ids = self.district_ids.filtered(lambda district: district.region_id.id in self.region_ids.ids)
    
    @api.onchange('district_ids')
    def _onchange_district_ids(self):
        if self.district_ids:
            self.region_ids |= self.district_ids.mapped('region_id')
        self.cooperative_ids = self.cooperative_ids.filtered(lambda coop: coop.district_id.id in self.district_ids.ids)
    
    @api.onchange('cooperative_ids')
    def _onchange_cooperative_ids(self):
        if self.cooperative_ids:
            self.district_ids |= self.cooperative_ids.mapped('district_id')
            
            if self.farmer_group_ids:
                self.farmer_group_ids = self.farmer_group_ids.filtered(lambda fg: fg.coop_id.id in self.cooperative_ids.ids)
    
    @api.onchange('farmer_group_ids')
    def _onchange_farmer_group_ids(self):
        if self.farmer_group_ids:
            self.cooperative_ids = self.farmer_group_ids.mapped('coop_id')
    
    @api.onchange('view_contracts', 'company_id', 'region_ids', 'district_ids', 'cooperative_ids', 'farmer_group_ids', 'season_id', 'product_id', 'expired_filter')
    def _compute_contracts(self):
        if self.view_contracts:
            self.contract_ids = self.env['offtake.agreement'].search(self._get_computed_contracts_domain())
        else:
            self.contract_ids = False
    
    def btn_confirm(self):
        self.ensure_one()
        
        if not self.view_contracts:
            raise ValidationError(_("Please select 'View Contracts' first to confirm the contracts that will be affected by the bulk operation!"))
        
        if not self.contract_ids:
            raise ValidationError(_("No contracts selected for the bulk operation!"))
        
    def _get_computed_contracts_domain(self):
        domain = []
        
        if self.company_id:
            domain.append( ('company_id','=',self.company_id.id) )
        
        if self.product_id:
            domain.append( ('contracted_crop_id','=',self.product_id.id) )
        
        if self.season_id:
            domain.append( ('season_id','=',self.season_id.id) )
        
        if self.expired_filter == 'expired':
            domain.append( ('expired_contract','=',True) )
        elif self.expired_filter == 'not_expired':
            domain.append( ('expired_contract','=',False) )
        
        if self.farmer_group_ids:
            domain.append( ('outgrower_id.farmer_group_id','in',self.farmer_group_ids.ids) )
        elif self.cooperative_ids:
            domain.append( ('outgrower_id.coop_id','in',self.cooperative_ids.ids) )
        elif self.district_ids:
            domain.append( ('outgrower_id.district_id','in',self.district_ids.ids) )
        elif self.region_ids:
            domain.append( ('outgrower_id.region_id','in',self.region_ids.ids) )
        
        return domain
        
    def _contracts_return_action(self, action_label, contracts=None):
        self.ensure_one()
        
        if not contracts:
            contracts = self.contract_ids
        
        return {
                'type': 'ir.actions.act_window',
                'name': action_label,
                'view_mode': 'list,form',
                'res_model': 'offtake.agreement',
                'domain': [('id', 'in', contracts.ids)],
            }
    

class BulkContractApprovalWizard(models.TransientModel):
    _name = 'bulk.contract.approval.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Approval'
    
    contract_ids = fields.Many2many(domain=[('contract_stage','=','draft')])
    show_expired_filter = fields.Boolean(default=False)
    
    def _get_computed_contracts_domain(self):
        return [('contract_stage','=','draft')] + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        self.contract_ids.confirm_offtake_agreement()
        return self._contracts_return_action(_('Contracts Confirmed'))
    

class BulkContractCloseWizard(models.TransientModel):
    _name = 'bulk.contract.close.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Close'
    
    contract_ids = fields.Many2many(domain=[('contract_stage','=','open')])
    
    def _get_computed_contracts_domain(self):
        return [('contract_stage','=','open')] + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        self.contract_ids.close_offtake_agreement()
        return self._contracts_return_action(_('Contracts Closed'))
    

class BulkContractCancelWizard(models.TransientModel):
    _name = 'bulk.contract.cancel.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Cancellation'
    
    state_filter = fields.Selection([('draft','Draft Only'),('open','Open Only')], 'Contract Status')
    contract_ids = fields.Many2many(domain=[('contract_stage','in',('draft','open'))])
    
    def _get_computed_contracts_domain(self):
        if self.state_filter:
            domain = [('contract_stage','=',self.state_filter)]
        else:
            domain = [('contract_stage','in',('draft','open'))]
        
        return domain + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        self.contract_ids.cancel_offtake_agreement()
        return self._contracts_return_action(_('Contracts Cancelled'))
    
    @api.onchange('state_filter')
    def _compute_contracts_on_state_filter(self):
        super()._compute_contracts()
    

class BulkContractRenewWizard(models.TransientModel):
    _name = 'bulk.contract.renew.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Renewal'
    
    contract_ids = fields.Many2many(domain=[('contract_stage','=','closed')])
    show_expired_filter = fields.Boolean(default=False)
    season_id = fields.Many2one(string='Closed Season', domain=[('status','in',('lock','closed'))], required=True)
    new_season_id = fields.Many2one('season', 'Renewal Season', domain=[('status','=','open')], required=True)
    
    @api.onchange('view_contracts')
    def _onchange_view_contracts(self):
        if self.view_contracts and not self.season_id:
            self.view_contracts = False
            return {'warning': {'title': _('Warning'), 'message': _("Please selected first the closed season on the filters to proceed.")}}
    
    def _get_computed_contracts_domain(self):
        return [('contract_stage','=','closed')] + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        
        contracts_env = self.env['offtake.agreement']
        new_contracts = self.env['offtake.agreement']
        
        for contract_to_renew in self.contract_ids:
            new_contracts += contract_to_renew.copy(default={'season_id': self.new_season_id.id})
        
        return self._contracts_return_action(_('Renewed Contracts'), contracts=new_contracts)
    

class BulkContractOfftakeWizard(models.TransientModel):
    _name = 'bulk.contract.offtake.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Off-Take'
    
    contract_ids = fields.Many2many(domain=[('has_offtake_order','=',False),('contract_stage','=','open'),('ready_for_harvest','=',True)])
    
    def _get_computed_contracts_domain(self):
        return [('has_offtake_order','=',False),('contract_stage','=','open'),('ready_for_harvest','=',True)] + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        
        po_ids = []
        
        purchase_orders_env = self.env['purchase.order']
        
        for contract in self.contract_ids:
            purchase_order = purchase_orders_env.create({
                'partner_id': contract.outgrower_id.id,
                'agrios_oa_id': contract.id,
            })
            purchase_order.onchange_partner_id()
            purchase_order._onchange_agrios_oa_id()
            
            po_ids.append(purchase_order.id)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Off-Take Orders',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', po_ids)],
        }
    

class BulkContractHarvestReadyWizard(models.TransientModel):
    _name = 'bulk.contract.harvest.ready.wizard'
    _inherit = ['bulk.contract.abstract.wizard']
    _description = 'Bulk Contract Harvest Ready'
    
    contract_ids = fields.Many2many(domain=[('contract_stage','=','open'),('ready_for_harvest','=',False)])
    show_expired_filter = fields.Boolean(default=False)
    
    def _get_computed_contracts_domain(self):
        return [('contract_stage','=','open'),('ready_for_harvest','=',False)] + super()._get_computed_contracts_domain()
    
    def btn_confirm(self):
        super().btn_confirm()
        self.contract_ids.set_ready_for_harvest()
        return self._contracts_return_action(_('Contracts Ready For Harvest'))
    