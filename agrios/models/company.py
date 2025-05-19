# -*- coding: utf-8 -*-

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'
    
    agrios_default_contract_needed = fields.Boolean('AgriOS Default Contract Required')
    agrios_close_expired_contracts = fields.Boolean('AgriOS Automatically Close Expired Contracts')
    agrios_allow_operations_out_of_phase = fields.Boolean('AgriOS Allow Operations Out Of Phase')
    agrios_payment_in_kind_optional = fields.Boolean('AgriOS Optional Payments In Kind')