# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CountryLocationLevel(models.Model):
    _name = "country.location.level"
    _description = "Country Area Level"
    _order = "country_id, level"

    country_id = fields.Many2one(
        comodel_name="res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    level = fields.Integer(required=True, default=1)
    name = fields.Char("Designation", required=True)

    _sql_constraints = [
        (
            "unique_country_level",
            "UNIQUE(country_id, level)",
            "Country / level must be unique!",
        ),
        (
            "unique_country_name",
            "UNIQUE(country_id, name)",
            "Country / level designation must be unique!",
        ),
        (
            "check_level_value",
            "CHECK(level > 0 AND level < 7)",
            "Level needs to be between 1 and 6!",
        ),
    ]
