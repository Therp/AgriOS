# -*- coding: utf-8 -*-

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'
    
    a_default_contract_required = fields.Boolean('Default Contract Required')
    close_expired_contracts = fields.Boolean('Automatically Close Expired Contracts')
    allow_operations_out_of_phase = fields.Boolean('Allow Operations Out Of Phase')
    payment_in_kind_optional = fields.Boolean('Optional Payments In Kind')