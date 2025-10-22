# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

FARMER_DOMAIN = (
    "[('is_farmer','=',True),"
    "('farmer_group_id','=',id),"
    "('farmer_stage','=','verified')]"
)


class FarmerGroup(models.Model):
    _name = "farmer.group"
    _description = "Farmer Group"
    _order = "name, agrios_area_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    country_id = fields.Many2one(
        "res.country",
        "Country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    agrios_area_id = fields.Many2one(
        comodel_name="agrios.area",
        domain="[('country_id', '=', country_id)]",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )
    chairperson_id = fields.Many2one(
        "res.partner",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    group_sec_id = fields.Many2one(
        "res.partner",
        "Secretary",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    group_treasurer_id = fields.Many2one(
        "res.partner",
        "Treasurer",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    member_ids = fields.One2many(
        "res.partner",
        "farmer_group_id",
        domain=[("is_farmer", "=", True), ("farmer_stage", "=", "verified")],
    )

    _sql_constraints = [
        (
            "unique_group_area_combination",
            "UNIQUE(name, agrios_area_id)",
            "A Group with this name already Exists in the specified Area",
        )
    ]
