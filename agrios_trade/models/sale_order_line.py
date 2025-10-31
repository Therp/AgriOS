# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    farmer_contract_line_id = fields.Many2one(related="order_id.farmer_contract_id")
    date_order = fields.Datetime(
        related="order_id.date_order", string="Order Date/Time", store=True, index=True
    )
    farmer_group_id = fields.Many2one(
        related="order_partner_id.farmer_group_id", store=True
    )

    @api.onchange("product_template_id")
    def _onchange_agrios_order(self):
        for order in self:
            if order.farmer_contract_line_id:
                order.product_uom_qty = max(
                    order.product_template_id.qty_per_acreage
                    * order.farmer_contract_line_id.contract_acreage,
                    1,
                )
