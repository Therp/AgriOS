from odoo import api, fields, models


class FarmerGroup(models.Model):
    _inherit = "farmer.group"
    _inherit = ["mail.thread", "mail.activity.mixin"]

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
