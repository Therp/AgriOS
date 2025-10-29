from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_farmer_contract = fields.Boolean(
        "Farmer Contracts", implied_group="agrios.group_farmer_contract"
    )
    group_farmers_training = fields.Boolean(
        "Farmer Trainings", implied_group="agrios.group_farmers_training"
    )
    group_farmers_certifications = fields.Boolean(
        "Farmer Certifications", implied_group="agrios.group_farmers_certifications"
    )
    group_payments_in_kind = fields.Boolean(
        "Payments In Kind", implied_group="agrios.group_payments_in_kind"
    )

    a_default_contract_required = fields.Boolean(
        related="company_id.a_default_contract_required",
        string="Default Contract Required",
        readonly=False,
    )
    close_expired_contracts = fields.Boolean(
        related="company_id.close_expired_contracts",
        string="Automatically Close Expired Contracts",
        readonly=False,
    )
    allow_operations_out_of_phase = fields.Boolean(
        related="company_id.allow_operations_out_of_phase",
        string="Allow Operations Out Of Phase",
        readonly=False,
    )
    payment_in_kind_optional = fields.Boolean(
        related="company_id.payment_in_kind_optional",
        string="Payments In Kind Optional Reconciliation",
        readonly=False,
    )

    @api.onchange("group_farmer_contract")
    def _onchange_group_farmer_contract(self):
        if not self.group_farmer_contract:
            self.a_default_contract_required = False
