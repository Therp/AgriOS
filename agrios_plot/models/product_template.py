# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    input_product = fields.Boolean(
        help="Product to be sold/given to farmers to help them"
        " produce harvestable products."
        " E.g. seeds, fertilizer, cultivation material, etc",
    )
    crop_product = fields.Boolean(
        string="Product is a crop",
        help="Products produced and harvested by a farmer."
        " E.g. pumpkins, chilli peppers, cocoa, etc",
    )
    seed_product = fields.Boolean(
        "Seed Variety", help="Select this field if this product is a seed."
    )
    harvest_product_type = fields.Selection(
        [
            ("perennial", "Perennial"),
            ("tree_crop", "Grow From Trees"),
        ],
        string="Crop Type",
        default="perennial",
    )
    tree_yield_ids = fields.One2many(
        "plant.age.yield", "crop_product_id", string="Tree Yields"
    )
    maturity_days = fields.Integer()
    estimated_yield = fields.Float("Estimated Yield (kgs)")
    qty_per_acreage = fields.Float("Default Qty")
    crop_product_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('crop_product','=',True),('id','not in',product_variant_ids)]",
    )
    land_area_uom = fields.Char(compute="_compute_farm_measure")
    related_inputs_ids = fields.Many2many(
        "product.product",
        domain="[('product_tmpl_id','!=',id),('input_product','=',True)]",
    )
    seed_ids = fields.Many2many(
        "product.product",
        string="Seed Varieties",
        compute="_compute_seed_ids",
        readonly=True,
    )

    def _compute_seed_ids(self):
        for prd_tmp in self:
            prd_tmp.seed_ids = prd_tmp.product_variant_ids.mapped("seed_ids")

    @api.depends("input_product", "crop_product")
    def _compute_farm_measure(self):
        ICP = self.env["ir.config_parameter"].sudo()
        plot_uom_id_str = ICP.get_param("geospatial_plot.plot_uom_id")  # string or False
    
        plot_uom = False
        if plot_uom_id_str:
            try:
                plot_uom = self.env["uom.uom"].browse(int(plot_uom_id_str))
            except (ValueError, TypeError):
                plot_uom = False
    
        for product in self:
            product.land_area_uom = f"/{plot_uom.name}" if plot_uom and plot_uom.exists() else ""

    @api.onchange("input_product")
    def _onchange_input_product(self):
        if self.input_product:
            self.sale_ok = True

    @api.onchange("crop_product")
    def _onchange_crop_product(self):
        if self.crop_product:
            self.purchase_ok = True
