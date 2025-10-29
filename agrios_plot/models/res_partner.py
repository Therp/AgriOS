# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_land_area_uom_domain(self):
        return [
            ("category_id.id", "=", self.env.ref("uom.uom_categ_surface").id),
            ("uom_type", "=", "bigger"),
        ]

    @api.model
    def _default_land_area_uom(self):
        land_area_uom = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("farmer_management.land_area_uom")
            or 0
        )
        if not land_area_uom:
            land_area_uom = self.env.ref("agrios.area_1", raise_if_not_found=False)
        return land_area_uom

    # farm details
    own_acreage = fields.Float(
        "Own Plot Acreage",
        compute="_compute_land_acreage",
        inverse="_inverse_farm_acreage",
        store=True,
        tracking=True,
    )
    leased_acreage = fields.Float(
        "Leased Plot Acreage",
        compute="_compute_land_acreage",
        inverse="_inverse_leased_acreage",
        store=True,
        tracking=True,
    )
    total_acreage = fields.Float(
        "Total Plot Acreage", compute="_compute_total_acreage", store=True
    )
    plot_ids = fields.One2many(
        "farmer.plot", "farmer_id", "Responsible Area", copy=False
    )
    crop_product_ids = fields.Many2many(
        "product.product",
        "res_partner_product_harvest_crops_rel",
        "partner_id",
        "product_id",
        domain=[("crop_product", "=", True)],
        string="Crop Products",
    )
    land_area_uom = fields.Many2one(
        "uom.uom",
        "Land Area Unit of Measure",
        domain=lambda self: self._get_land_area_uom_domain(),
        default=lambda self: self._default_land_area_uom(),
        tracking=True,
    )

    @api.depends("plot_ids", "plot_ids.plot_size")
    def _compute_land_acreage(self):
        for farmer in self:
            if farmer.plot_ids:
                farmer.own_acreage = sum(
                    farmer.plot_ids.filtered(lambda plot: plot.is_owner).mapped(
                        "plot_size"
                    )
                )
                farmer.leased_acreage = sum(
                    farmer.plot_ids.filtered(lambda plot: not plot.is_owner).mapped(
                        "plot_size"
                    )
                )
            else:
                farmer.own_acreage = farmer.leased_acreage = 0.0

    def _inverse_farm_acreage(self):
        """Allows manual updates to farm_acreage via import"""
        for record in self:
            record.own_acreage = record.own_acreage

    def _inverse_leased_acreage(self):
        """Allows manual updates to leased_acreage via import"""
        for record in self:
            record.leased_acreage = record.leased_acreage

    @api.depends("own_acreage", "leased_acreage")
    def _compute_total_acreage(self):
        for rec in self:
            rec.total_acreage = rec.own_acreage + rec.leased_acreage

    @api.model
    def web_search_read(
        self, domain, specification, offset=0, limit=None, order=None, count_limit=None
    ):
        if self._context.get("filter_duplicate_identification"):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id
                AND ptn1.farmer_id_number = ptn2.farmer_id_number
                WHERE ptn1.farmer_id_number IS NOT NULL
            """)
            ident_duplicate_ids = [ptn[0] for ptn in self._cr.fetchall()]
            if domain:
                domain = ["&", ("id", "in", ident_duplicate_ids)] + domain
            else:
                domain = [("id", "in", ident_duplicate_ids)]

        if self._context.get("filter_duplicate_phone"):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id
                AND ptn1.phone = ptn2.phone
                WHERE ptn1.phone IS NOT NULL
            """)
            phone_duplicate_ids = [ptn[0] for ptn in self._cr.fetchall()]
            if domain:
                domain = ["&", ("id", "in", phone_duplicate_ids)] + domain
            else:
                domain = [("id", "in", phone_duplicate_ids)]

        return super().web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

    def action_create_farm(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("New Plot Of %s") % self.display_name,
            "res_model": "farmer.plot",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_farmer_id": self.id,
                "default_name": _(
                    "%(display_name)s Farm #%(plot_count)d",
                    display_name=self.display_name,
                    plot_count=len(self.plot_ids) + 1,
                ),
                "plot_partner_readonly": True,
            },
        }
