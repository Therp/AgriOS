from odoo import api, fields, models


class FarmerInteraction(models.Model):
    _name = "farmer.interaction"
    _description = "Farmer Interaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "interaction_date DESC"

    name = fields.Char("Summary", required=True, tracking=True)
    interaction_date = fields.Date(
        "Date", required=True, tracking=True, index=True, default=fields.Date.today()
    )
    farmer_id = fields.Many2one(
        "res.partner",
        "Farmer",
        domain=[("is_farmer", "=", True)],
        tracking=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "farmer.contract", domain="[('farmer_id','=',farmer_id)]", tracking=True
    )
    interaction_type = fields.Selection(
        selection=[
            ("visit", "Visit"),
            ("call", "Call"),
            ("other", "Other"),
        ],
        required=True,
        tracking=True,
    )
    notes = fields.Text(required=True)
    active = fields.Boolean(default=True, tracking=True)

    @api.onchange("farmer_id")
    def _onchange_farmer_id(self):
        if self.contract_id and self.contract_id.farmer_id != self.farmer_id:
            self.contract_id = False
