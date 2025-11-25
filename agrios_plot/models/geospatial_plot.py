# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GeospatialPlot(models.Model):
    """Add agricultural attributes to plot."""

    _inherit = "geospatial.plot"

    is_agricultural_plot = fields.Boolean()
    year_established = fields.Char(tracking=True)
    registration_year = fields.Integer("Year of Registration")
    located_in_protected_area = fields.Boolean()
    plot_condition = fields.Selection(
        selection=[
            ("bad", "Bad"),
            ("needsimprovement", "Needs Improvement"),
            ("good", "Good"),
            ("verygood", "Very Good"),
        ],
        default=False,
    )
    intercropping = fields.Boolean()
    subplot_ids = fields.One2many("farmer.plot.crop.area", "plot_id", string="Subplots")
    main_road = fields.Char()
    main_road_distance = fields.Float("Main Road Distance (km)")

    @api.constrains("year_established")
    def _check_year_of_farm_establishment(self):
        for rec in self:
            year = rec.year_established
            if year:
                if not year.isdigit():
                    raise ValidationError(_("Year must be digits only!"))
                if len(year) != 4:
                    raise ValidationError(_("Year must be 4 digits!"))
