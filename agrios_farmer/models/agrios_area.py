# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AdministrationLocations(models.Model):
    _name = "agrios.area"
    _description = "Area"
    _order = "country_id, name"
    _parent_store = True

    country_location_level_id = fields.Many2one(
        comodel_name="country.location.level",
        required=True,
    )
    country_id = fields.Many2one(
        comodel_name="res.country",
        related="country_location_level_id.country_id",
    )
    level = fields.Integer(related="country_location_level_id.level")
    name = fields.Char(required=True)
    # TODO RP: Make computed fields to set required and domain for parent_id.
    #  - Parent must be one level higher then own level;
    #  - Required when not the highest level.
    parent_id = fields.Many2one(
        comodel_name="agrios.area",
        string="Parent Area",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(index=True)
    manager_id = fields.Many2one("res.partner", "Area Manager")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_name",
            "UNIQUE(parent_id, name)",
            "A location with this name already exists in the same area!",
        ),
    ]

    @api.depends("parent_id")
    def _compute_display_name(self):
        """Return the categories' display name, including their direct
        parent by default.
        """
        for this in self:
            names = []
            current = this
            while current:
                names.append(current.name or "")
                current = current.parent_id
            this.display_name = " / ".join(reversed(names))

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if operator.endswith("like"):
            return [("id", "child_of", self._search(list(domain)))]
        return domain
