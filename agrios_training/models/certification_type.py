# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CertificationType(models.Model):
    _name = "certification.type"
    _description = "Certification Type"
    _order = "name"

    name = fields.Char("Certification Type", required=True)
    certifying_organisation_id = fields.Many2one(
        "res.partner", "Certifying Organization", ondelete="restrict"
    )
    validity_period = fields.Integer("Validity (Months)", default=12, required=True)
    style = fields.Selection(
        [
            ("info", "Blue"),
            ("muted", "Grey"),
            ("success", "Green"),
            ("warning", "Orange"),
            ("danger", "Red"),
        ],
        "Color Style",
    )
    active = fields.Boolean(default=True)
    certification_ids = fields.One2many("farmer.certification", "certification_type_id")
    farmer_count = fields.Integer("Certified Farmers", compute="_compute_farmer_count")

    _sql_constraints = [
        (
            "_check_validity",
            "CHECK(validity_period > 0)",
            "Validity Period MUST be greater than zero",
        ),
    ]

    def _compute_farmer_count(self):
        for rec in self:
            rec.farmer_count = len(rec.certification_ids.mapped("farmer_id"))
