# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FarmerPlot(models.Model):
    _name = "farmer.plot"
    _inherit = ["mail.thread"]
    _description = "Farmer Plot"
    _order = "farmer_id"

    def _get_land_area_uom_domain(self):
        surface_uom = self.env.ref("uom.uom_categ_surface", raise_if_not_found=False).id
        return [("category_id.id", "=", surface_uom), ("uom_type", "=", "bigger")]

    def _get_default_land_area_uom(self):
        land_area_uom_config = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("farmer_management.land_area_uom")
        )
        return (
            land_area_uom_config
            and int(land_area_uom_config)
            or self.env.ref("agrios.area_1", raise_if_not_found=False)
        )

    name = fields.Char(required=True, tracking=True)
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    agrios_area_id = fields.Many2one(
        comodel_name="agrios.area",
        domain="[('country_id', '=', country_id)]",
    )
    plot_shape_type = fields.Selection(
        selection=[
            ("circle", "Circle"),
            ("polygon", "Polygon"),
            ("rectangle", "Rectangle"),
        ],
    )
    plot_description = fields.Text("Description")
    farmer_id = fields.Many2one(
        "res.partner",
        domain="[('is_farmer','=',True)]",
        required=True,
        ondelete="cascade",
        tracking=True,
        index=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    year_established = fields.Char(tracking=True)
    registration_year = fields.Integer("Year of Registration")
    is_owner = fields.Boolean(
        "Owned By Farmer",
        help="If the Farmer owns the plot of land or not",
        default=True,
    )
    located_in_protected_area = fields.Boolean()
    plot_uom_id = fields.Many2one(
        "uom.uom",
        domain=_get_land_area_uom_domain,
        default=_get_default_land_area_uom,
        tracking=True,
        readonly=True,
    )
    plot_size = fields.Float(required=True, tracking=True)
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
    gps_location = fields.Char(tracking=True)
    plot_polygon = fields.Json()
    country_code = fields.Char(
        compute="_compute_country_code",
        default=lambda self: self.env.company.country_id.code or False,
    )

    def _compute_country_code(self):
        country_code = self.env.company.country_id.code or False
        for rpa in self:
            rpa.country_code = country_code

    @api.constrains("year_established")
    def _check_year_of_farm_establishment(self):
        for rec in self:
            year = rec.year_established

            if year:
                if not year.isdigit():
                    raise ValidationError(_("Year must be digits only!"))
                if len(year) != 4:
                    raise ValidationError(_("Year must be 4 digits!"))

    @api.constrains("plot_size")
    def _check_plot_size(self):
        for rec in self:
            if rec.plot_size < 0.0:
                raise ValidationError(_("Farm size of plot needs to be higher than 0."))
