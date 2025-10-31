# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class FarmerGroup(models.Model):
    _name = "farmer.group"
    _inherit = ["farmer.group", "mail.thread", "mail.activity.mixin"]

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    total_due = fields.Monetary(
        "Group Amount Due",
        compute="_compute_total_due",
        help="Sum amount due of all the group members",
    )

    @api.depends("member_ids")
    def _compute_total_due(self):
        for farm_group in self:
            farm_group.total_due = 0.0
            for member in farm_group.member_ids:
                for aml in member.unreconciled_aml_ids:
                    if aml.company_id == farm_group.company_id and not aml.blocked:
                        farm_group.total_due += aml.amount_residual
