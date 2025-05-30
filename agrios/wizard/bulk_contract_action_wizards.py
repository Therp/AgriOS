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
    
    country_id = fields.Many2one('res.country', string='Country')
    loc_area_6_ids = fields.Many2many('area.level.6', domain="[('country_id','=', country_id)]", string='Location Area 6')
    loc_area_5_ids = fields.Many2many('area.level.5', domain="[('country_id','=', country_id)]", string='Location Area 5')
    loc_area_4_ids = fields.Many2many('area.level.4', domain="[('country_id','=', country_id)]", string='Location Area 4')
    loc_area_3_ids = fields.Many2many('area.level.3', domain="[('country_id','=', country_id)]", string='Location Area 3')
    loc_area_2_ids = fields.Many2many('area.level.2', domain="[('country_id','=', country_id)]", string='Location Area 2')
    loc_area_1_ids = fields.Many2many('area.level.1', domain="[('country_id','=', country_id)]", string='Location Area 1')
    farmer_group_ids = fields.Many2many('farmer.group', string='Farmer Groups')

    loc_area_1_label = fields.Char('Location Area 1 Label', compute="_compute_loc_area_details")
    loc_area_2_label = fields.Char('Location Area 2 Label', compute="_compute_loc_area_details")
    loc_area_3_label = fields.Char('Location Area 3 Label', compute="_compute_loc_area_details")
    loc_area_4_label = fields.Char('Location Area 4 Label', compute="_compute_loc_area_details")
    loc_area_5_label = fields.Char('Location Area 5 Label', compute="_compute_loc_area_details")
    loc_area_6_label = fields.Char('Location Area 6 Label', compute="_compute_loc_area_details")
    loc_area_max_level = fields.Integer('Max Location Area', compute="_compute_loc_area_details")
    
    season_id = fields.Many2one('season', 'Season', domain=[('status','in',('open','lock'))])
    product_id = fields.Many2one('product.product', 'Harvestable Product', domain=[('harvest_product','=',True)])
    expired_filter = fields.Selection([('expired','Expired Only'),('not_expired','Not Expired Only')], 'Expired Contracts')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            self.loc_area_6_ids = self.loc_area_6_ids.filtered(lambda rec: rec.country_id.id == self.country_id.id)
    
    @api.onchange('loc_area_3_ids')
    def _onchange_loc_area_3_ids(self):
        self.loc_area_2_ids = self.loc_area_2_ids.filtered(lambda loc_area_2: loc_area_2.parent_id.id in self.loc_area_3_ids.ids)
    
    @api.onchange('loc_area_2_ids')
    def _onchange_loc_area_2_ids(self):
        if self.loc_area_2_ids:
            self.loc_area_3_ids |= self.loc_area_2_ids.mapped('parent_id')
        self.loc_area_1_ids = self.loc_area_1_ids.filtered(lambda loc_area_1: loc_area_1.parent_id.id in self.loc_area_2_ids.ids)
    
    @api.onchange('loc_area_1_ids')
    def _onchange_loc_area_1_ids(self):
        if self.loc_area_1_ids:
            self.loc_area_2_ids |= self.loc_area_1_ids.mapped('parent_id')
            
            if self.farmer_group_ids:
                self.farmer_group_ids = self.farmer_group_ids.filtered(lambda fg: fg.loc_area_1_id.id in self.loc_area_1_ids.ids)
    
    @api.onchange('farmer_group_ids')
    def _onchange_farmer_group_ids(self):
        if self.farmer_group_ids:
            self.loc_area_1_ids = self.farmer_group_ids.mapped('loc_area_1_id')
    
    @api.onchange('view_contracts', 'company_id', 'loc_area_3_ids', 'loc_area_2_ids', 'loc_area_1_ids', 'farmer_group_ids', 'season_id', 'product_id', 'expired_filter')
    def _compute_contracts(self):
        if self.view_contracts:
            self.contract_ids = self.env['offtake.agreement'].search(self._get_computed_contracts_domain())
        else:
            self.contract_ids = False

    @api.onchange('country_id')
    def _compute_loc_area_details(self):
        cll_env = self.env['country.location.level']
        for action in self:
            country_id = action.country_id
            loc_details, max_level = cll_env._get_country_details(action.country_id.id)
            action.loc_area_1_label = loc_details[1]
            action.loc_area_2_label = loc_details[2]
            action.loc_area_3_label = loc_details[3]
            action.loc_area_4_label = loc_details[4]
            action.loc_area_5_label = loc_details[5]
            action.loc_area_6_label = loc_details[6]
            action.loc_area_max_level = max_level
    
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
        elif self.loc_area_1_ids:
            domain.append( ('outgrower_id.loc_area_1_id','in',self.loc_area_1_ids.ids) )
        elif self.loc_area_2_ids:
            domain.append( ('outgrower_id.loc_area_2_id','in',self.loc_area_2_ids.ids) )
        elif self.loc_area_3_ids:
            domain.append( ('outgrower_id.loc_area_3_id','in',self.loc_area_3_ids.ids) )
        
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
    