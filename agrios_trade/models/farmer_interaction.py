# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class FarmerInteraction(models.Model):
    _inherit = "farmer.interaction"

    contract_id = fields.Many2one(
        "farmer.contract", domain="[('farmer_id','=',farmer_id)]", tracking=True
    )

    @api.onchange("farmer_id")
    def _onchange_farmer_id(self):
        if self.contract_id and self.contract_id.farmer_id != self.farmer_id:
            self.contract_id = False
