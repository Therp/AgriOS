# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    seed_ids = fields.One2many(
        "product.product",
        "crop_product_id",
        "Seed Varieties",
        domain=[("seed_product", "=", True)],
        readonly=True,
    )
