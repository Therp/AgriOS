# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    _rec_names_search = [
        "complete_name",
        "email",
        "ref",
        "vat",
        "company_registry",
        "phone",
        "farmer_ref",
    ]

    # Basic farmer details
    farmer_stage = fields.Selection(
        [("draft", "Draft"), ("verified", "Verified")],
        default="draft",
        copy=False,
    )

    is_farmer = fields.Boolean("Farmer", default=False)
    farmer_ref = fields.Char("Farmer Reference", default="/", readonly=True, copy=False)
    farmer_group_id = fields.Many2one(
        comodel_name="farmer.group",
        ondelete="restrict",
        tracking=True,
    )
    agrios_area_id = fields.Many2one(
        comodel_name="agrios.area",
        domain="[('country_id', '=', country_id)]",
    )
    highest_education_id = fields.Many2one(
        comodel_name="partner.education",
        ondelete="restrict",
        tracking=True,
    )
    interactions_count = fields.Integer(
        compute="_compute_interactions_count", string="Interactions"
    )
    responsible_farmer_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Farmers Responsible",
        compute="_compute_responsible_farmer_ids",
    )
    # Override attributes of standard fields
    country_id = fields.Many2one(
        required=True, default=lambda self: self.env.company.country_id
    )
    # extra farmer info
    family_size = fields.Integer()
    next_of_kin = fields.Char()
    nok_id = fields.Char(string="NOK ID")
    nok_phone = fields.Char(string="NOK Phone")

    @api.depends("farmer_ref")
    def _compute_display_name(self):
        ret = super()._compute_display_name()
        for partner in self:
            if partner.farmer_ref and partner.farmer_ref != "/":
                partner.display_name = (
                    f"[{partner.farmer_ref}] {partner.display_name or ''}"
                )
        return ret

    def _compute_interactions_count(self):
        for partner in self:
            partner.interactions_count = self.env["farmer.interaction"].search_count(
                [("farmer_id", "=", partner.id)]
            )

    def action_verify_farmer(self):
        for farmer in self:
            vals = farmer._prepare_verify_farmer_vals()
            farmer.with_context(mail_notrack=True).write(vals)

    def _prepare_verify_farmer_vals(self):
        self.ensure_one()
        vals = {"farmer_stage": "verified"}
        if not self.farmer_ref or self.farmer_ref == "/":
            vals["farmer_ref"] = self.env["ir.sequence"].next_by_code("farmer")
        return vals

    def action_view_interactions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Interactions",
            "res_model": "farmer.interaction",
            "view_mode": "list,form",
            "domain": [("farmer_id", "=", self.id)],
            "context": {"default_farmer_id": self.id},
        }
