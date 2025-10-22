# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


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
