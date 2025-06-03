# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ConfirmContractsWizard(models.TransientModel):
    _name = 'multiple.confirm.draft.contracts.wizard'
    _description = 'Confirm Multiple Contracts'
    
    contract_ids = fields.Many2many('farmer.contract', string='Draft Contracts To Confirm', domain=[('contract_stage','=','draft')])
    
    @api.model
    def default_get(self, default_fields):
        ret = super().default_get(default_fields)
        
        if 'contract_ids' in default_fields:
            if ret.get('contract_ids'):
                contract_ids = ret['contract_ids']
            elif self._context.get('active_model') == 'farmer.contract':
                contract_ids = self._context.get('active_ids')
            else:
                contract_ids = []
            
            self._cr.execute("SELECT id FROM farmer_contract WHERE contract_stage = 'draft' and id IN %s", (tuple(contract_ids),))
            draft_contract_ids = [c[0] for c in self._cr.fetchall()]
            
            if not draft_contract_ids:
                raise ValidationError(_('No draft contracts selected!'))
            
            ret['contract_ids'] = [(6,0,draft_contract_ids)]
        
        return ret
    
    def confirm_contracts(self):
        draft_contracts = self.contract_ids.filtered(lambda cont: cont.contract_stage == 'draft')
        draft_contracts.confirm_farmer_contract()
        
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("All %d contracts have been confirmed.") % len(draft_contracts),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        