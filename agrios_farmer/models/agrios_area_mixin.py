# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AgriosAreaMixin(models.AbstractModel):
    _name = "agrios.area.mixin"
    _description = "Allows to add area link to any object with a location." ""

    # Country is essential before selecting an area.
    country_id = fields.Many2one(
        comodel_name="res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    # Field already defined in partner, but we need it also in other places.
    country_code = fields.Char(related="country_id.code")
    # Area is a writable stored computed field,
    # to allow automatic reset when country changes.
    agrios_area_id = fields.Many2one(
        comodel_name="agrios.area",
        domain="[('country_id', '=', country_id)]",
        compute="_compute_agrios_area_id",
        readonly=False,
        store=True,
    )
    agrios_area_label = fields.Char(compute="_compute_agrios_area_label")
    # Area can only be selected when levels for country defined.
    agrios_area_allowed = fields.Boolean(compute="_compute_agrios_area_allowed")

    @api.depends("country_id")
    def _compute_agrios_area_id(self):
        """Clear field when incompatible country selected."""
        for this in self:
            if not this.agrios_area_id:
                continue
            if not this.country_id or this.country_id != this.agrios_area_id.country_id:
                this.agrios_area_id = False

    @api.depends("country_id", "agrios_area_id")
    def _compute_agrios_area_label(self):
        """Only allow area when country filled, and present in levels."""
        Level = self.env["country.location.level"]
        for this in self:
            if this.agrios_area_id:
                label = this.agrios_area_id.country_location_level_id.name
            elif this.country_id:
                lowest_level = Level.search(
                    [("country_id", "=", this.country_id.id)],
                    order="level desc",
                    limit=1,
                )
                label = lowest_level.name if lowest_level else False
            else:
                label = False
            this.agrios_area_label = label

    @api.depends("country_id")
    def _compute_agrios_area_allowed(self):
        """Only allow area when country filled, and present in levels."""
        Level = self.env["country.location.level"]
        for this in self:
            this.agrios_area_allowed = this.country_id and Level.search(
                [("country_id", "=", this.country_id.id)], limit=1
            )
