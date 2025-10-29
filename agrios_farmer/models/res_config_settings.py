# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_farmer_interactions = fields.Boolean(
        "Farmer Interactions", implied_group="agrios_farmer.group_farmer_interactions"
    )
