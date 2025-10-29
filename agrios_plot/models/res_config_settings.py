# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def _get_land_area_uom_domain(self):
        return [
            ("category_id.id", "=", self.env.ref("uom.uom_categ_surface").id),
            ("uom_type", "=", "bigger"),
        ]

    group_seed_varieties = fields.Boolean(
        "Seed Varieties", implied_group="agrios_plot.group_seed_varieties"
    )
    group_plot_management = fields.Boolean(
        "Plot Management", implied_group="agrios_plot.group_plot_management"
    )
    group_plot_maps = fields.Boolean(
        "Plot On Maps", implied_group="agrios_plot.group_plot_maps"
    )

    land_area_uom = fields.Many2one(
        "uom.uom",
        string="Land Area Unit of Measure",
        config_parameter="farmer_management.land_area_uom",
        domain=lambda self: self._get_land_area_uom_domain(),
        default=lambda self: self.env.ref(
            "agrios_plot.uom_surface_acre", raise_if_not_found=False
        ),
    )
    max_plot_size = fields.Float(config_parameter="farmer_management.max_plot_size")

    @api.constrains("land_area_uom")
    def _check_land_area_uom(self):
        ICP = self.env["ir.config_parameter"].sudo()
        Partner = self.env["res.partner"]
        for record in self:
            if record.land_area_uom.id == (
                int(ICP.get_param("farmer_management.land_area_uom") or 0)
                or self.env.ref("agrios_plot.uom_surface_acre").id
            ):
                continue
            if Partner.search_count([("is_farmer", "=", True)]) > 0:
                raise ValidationError(
                    _("You cannot change the UoM once an farmer has been registered.")
                )
