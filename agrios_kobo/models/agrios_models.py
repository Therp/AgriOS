from odoo import fields, models


class Farmer(models.Model):
    _inherit = "res.partner"

    farmer_group_idx = fields.Integer(
        related="farmer_group_id.id", string="Farmers Group ID"
    )
