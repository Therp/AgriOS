# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    payment_in_kind_invoice_ids = fields.Many2many('account.move', compute='_compute_payment_in_kind')
    payment_in_kind_full_amount = fields.Monetary('Payment In Kind Full Amount', compute='_compute_payment_in_kind')
    payment_in_kind_amount = fields.Monetary('Payment In Kind Deduct Amount', compute='_compute_payment_in_kind')
    apply_payment_in_kind = fields.Boolean('Deduct Payment In Kind Amount', compute='_compute_apply_payment_in_kind', precompute=True, store=True)
    payment_in_kind_optional = fields.Boolean(related='company_id.oms_payment_in_kind_optional')
    
    @api.depends('currency_id')
    def _compute_payment_in_kind(self):
        for wizard in self:
            if wizard.currency_id and wizard.partner_id and wizard.payment_type == 'outbound':
                wizard.payment_in_kind_full_amount = 0.0
                wizard.payment_in_kind_invoice_ids = self.env['account.move'].search([('partner_id','=',wizard.partner_id.id),('payment_in_kind','=',True),('amount_residual','>',0.0),('state','=','posted')], order='invoice_date ASC, id ASC')
                
                for payment_in_kind_invoice in wizard.payment_in_kind_invoice_ids:
                    amount = payment_in_kind_invoice.amount_residual
                    if payment_in_kind_invoice.currency_id != wizard.currency_id:
                        amount = payment_in_kind_invoice.currency_id._convert(amount, wizard.currency_id, company=wizard.company_id)
                    wizard.payment_in_kind_full_amount += amount
                
                if wizard.payment_in_kind_full_amount:
                    batch_result = wizard._get_batches()[0]
                    total_amount_residual_in_wizard_currency = wizard._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount=False)[0]
                    wizard.payment_in_kind_amount = min(wizard.payment_in_kind_full_amount, total_amount_residual_in_wizard_currency)
                else:
                    wizard.payment_in_kind_amount = 0.0
                
            else:
                wizard.payment_in_kind_invoice_ids = wizard.payment_in_kind_full_amount = wizard.payment_in_kind_amount = False
    
    @api.depends('payment_in_kind_amount')
    def _compute_apply_payment_in_kind(self):
        for wizard in self:
            wizard.apply_payment_in_kind = bool(wizard.payment_in_kind_amount)
    
    @api.onchange('apply_payment_in_kind')
    def _onchange_apply_payment_in_kind(self):
        if self.payment_in_kind_amount:
            if self.apply_payment_in_kind:
                self.amount -= self.payment_in_kind_amount
            else:
                self.amount += self.payment_in_kind_amount
    
    @api.depends('apply_payment_in_kind')
    def _compute_payment_difference(self):
        super()._compute_payment_difference()
        
        for wizard in self:
            if wizard.apply_payment_in_kind:
                wizard.payment_difference -= wizard.payment_in_kind_amount
    
    def _create_payments(self):
        payments = super()._create_payments()
        
        if self.apply_payment_in_kind:
            account_moves_env = self.env['account.move'].sudo()
            
            for bill in self.line_ids.mapped('move_id'):
                for invoice in self.payment_in_kind_invoice_ids:
                    invoice_bill_amount_to_reconcile = min(invoice.amount_residual, bill.amount_residual)
                    
                    if invoice_bill_amount_to_reconcile:
                        inv_debit_line = invoice.line_ids.filtered(lambda invl: invl.debit).sorted('debit')
                        bill_credit_line = bill.line_ids.filtered(lambda invl: invl.credit).sorted('credit')
                        if inv_debit_line and bill_credit_line:
                            inv_debit_line = inv_debit_line[-1]
                            bill_credit_line = bill_credit_line[-1]
                            
                            reconcile_entry = account_moves_env.create({
                                'move_type': 'entry',
                                'ref': _('Payment In Kind Reconciliation') + (' - ' + bill.name + ' - ' + invoice.name),
                                'date': fields.Date.today(),
                                'company_id': self.company_id.id,
                                'currency_id': self.currency_id.id,
                                'line_ids': [
                                    (0,0,{
                                        'account_id': inv_debit_line.account_id.id,
                                        'name': _('Debit Reconciliation'),
                                        'credit': invoice_bill_amount_to_reconcile,
                                        'partner_id': self.partner_id.id,
                                    }),
                                    (0,0,{
                                        'account_id': bill_credit_line.account_id.id,
                                        'name': _('Credit Reconciliation'),
                                        'debit': invoice_bill_amount_to_reconcile,
                                        'partner_id': self.partner_id.id,
                                    })
                                ],
                            })
                            reconcile_entry.action_post()
                            (inv_debit_line + reconcile_entry.line_ids.filtered(lambda rec_line: rec_line.credit)).reconcile()
                            (bill_credit_line + reconcile_entry.line_ids.filtered(lambda rec_line: rec_line.debit)).reconcile()
        
        return payments
    