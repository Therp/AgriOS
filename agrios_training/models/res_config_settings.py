# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    group_farmer_training = fields.Boolean(
        "Farmer Trainings", implied_group="agrios_training.group_farmer_training"
    )
    group_farmer_certification = fields.Boolean(
        "Farmer Certifications",
        implied_group="agrios_training.group_farmer_certification",
    )
