from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    a_default_contract_required = fields.Boolean("Default Contract Required")
    close_expired_contracts = fields.Boolean("Automatically Close Expired Contracts")
    allow_operations_out_of_phase = fields.Boolean()
    payment_in_kind_optional = fields.Boolean("Optional Payments In Kind")
