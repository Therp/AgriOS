# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    farmer_contract_line_id = fields.Many2one(
        "farmer.contract", related="order_id.farmer_contract_id"
    )
    date_order = fields.Datetime(store=True, index=True)
    farmer_group_id = fields.Many2one(related="partner_id.farmer_group_id", store=True)

    def _compute_price_unit_and_date_planned_and_name(self):
        ret = super()._compute_price_unit_and_date_planned_and_name()
        if (
            self.order_id.farmer_contract_id
            and self.product_id
            and self.product_id == self.order_id.farmer_contract_id.contracted_crop_id
        ):
            self.price_unit = self.order_id.farmer_contract_id.contracted_unit_price
        return ret
