# -*- coding: utf-8 -*-

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'
    
    oms_default_contract_needed = fields.Boolean('OMS Default Contract Required')
    oms_close_expired_contracts = fields.Boolean('OMS Automatically Close Expired Contracts')
    oms_allow_operations_out_of_phase = fields.Boolean('OMS Allow Operations Out Of Phase')
    oms_payment_in_kind_optional = fields.Boolean('OMS Optional Payments In Kind')