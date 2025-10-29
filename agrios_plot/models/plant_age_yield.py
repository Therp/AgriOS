# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PlantAgeYield(models.Model):
    _name = "plant.age.yield"
    _description = "Projected Plant Age Yields"
    _order = "crop_product_id, age"

    crop_product_id = fields.Many2one(
        "product.template",
        string="Crop Product",
        domain=[
            ("crop_product", "=", True),
            ("harvest_product_type", "=", "tree_crop"),
        ],
        required=True,
        ondelete="cascade",
        index=True,
    )
    age = fields.Integer(
        "Age From",
        required=True,
        help="The age from when the product will have the set yield",
    )
    annual_yield = fields.Float(
        "Annual Yield per Tree (KG)", required=True, digits=(10, 2)
    )

    _sql_constraints = [
        (
            "unique_product_age",
            "UNIQUE(crop_product_id, age)",
            "A yield record for this crop and age already exists.",
        ),
        ("positive_age", "CHECK(age >= 0)", "The age cannot be a negative number."),
        (
            "positive_yield",
            "CHECK(annual_yield >= 0)",
            "The annual yield cannot be a negative number.",
        ),
    ]
