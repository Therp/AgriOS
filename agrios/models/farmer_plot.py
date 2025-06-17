# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FarmerPlot(models.Model):
    _name = 'farmer.plot'
    _inherit = ["mail.thread"]
    _description = 'Farmer Plot'
    _order = 'partner_id'
    
    def _get_land_area_uom_domain(self):
        surface_uom = self.env.ref('uom.uom_categ_surface', raise_if_not_found=False).id
        return [('category_id.id', '=', surface_uom),('uom_type', '=', 'bigger')]
    
    def _get_default_land_area_uom(self):
        land_area_uom_config = self.env['ir.config_parameter'].sudo().get_param('farmer_management.land_area_uom')
        return land_area_uom_config and int(land_area_uom_config) or self.env.ref('agrios.area_1', raise_if_not_found=False)
    
    name = fields.Char('Name', required=True, tracking=True)
    
    gshape_name = fields.Char('Gshape Name')
    plot_shape_type = fields.Selection([('circle', 'Circle'),('polygon', 'Polygon'),('rectangle', 'Rectangle')], 'Plot Shape Type')
    gshape_description = fields.Text('Description')
    
    partner_id = fields.Many2one('res.partner', 'Farmer', domain="[('is_farmer','=',True)]", required=True, ondelete='cascade', tracking=True, index=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    year_established = fields.Char('Year Established', tracking=True)
    registration_year = fields.Integer('Year of Registration')
    is_owner = fields.Boolean('Owned By Farmer', help='If the Farmer owns the plot of land or not', default=True)
    located_in_protected_area = fields.Boolean('Located in Protected Area')
    plot_uom_id = fields.Many2one('uom.uom', 'Plot UOM', domain=_get_land_area_uom_domain, default=_get_default_land_area_uom, tracking=True, readonly=True)
    plot_size = fields.Float('Plot Size', required=True, tracking=True)
    plot_condition = fields.Selection([('bad', 'Bad'),('needsimprovement','Needs Improvement'),('good','Good'),('verygood','Very Good')], default=False, string='Plot Condition')
    intercropping = fields.Boolean('Intercropping')
    subplot_ids = fields.One2many('farmer.plot.crop.area', 'plot_id', string='Subplots')
    
    loc_area_1_id = fields.Many2one('area.level.1', 'Area Level 1', tracking=True)
    loc_area_2_id = fields.Many2one('area.level.2', 'Area Level 2', ondelete='restrict', tracking=True)
    loc_area_3_id = fields.Many2one('area.level.3', 'Area Level 3', ondelete='restrict', tracking=True)
    loc_area_4_id = fields.Many2one('area.level.4', 'Area Level 4', ondelete='restrict', tracking=True)
    loc_area_5_id = fields.Many2one('area.level.5', 'Area Level 5', ondelete='restrict', tracking=True)
    loc_area_6_id = fields.Many2one('area.level.6', 'Area Level 6', ondelete='restrict', tracking=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    
    loc_area_1_label = fields.Char('Area Level 1 Label', compute="_compute_loc_area_details")
    loc_area_2_label = fields.Char('Area Level 2 Label', compute="_compute_loc_area_details")
    loc_area_3_label = fields.Char('Area Level 3 Label', compute="_compute_loc_area_details")
    loc_area_4_label = fields.Char('Area Level 4 Label', compute="_compute_loc_area_details")
    loc_area_5_label = fields.Char('Area Level 5 Label', compute="_compute_loc_area_details")
    loc_area_6_label = fields.Char('Area Level 6 Label', compute="_compute_loc_area_details")
    loc_area_max_level = fields.Integer('Max Area Level', compute="_compute_loc_area_details")
    
    main_road = fields.Char('Main Road')
    main_road_distance = fields.Float('Main Road Distance (km)')
    gps_location = fields.Char('GPS Location', tracking=True)
    
    plot_polygon = fields.Json('Plot Polygon')
    country_code = fields.Char(compute='_compute_country_code', default=lambda self: self.env.company.country_id.code or False)
    
    def _compute_country_code(self):
        country_code = self.env.company.country_id.code or False
        for rpa in self:
            rpa.country_code = country_code
    
    def init(self):
        super().init()
        self._cr.execute("""
            UPDATE farmer_plot
            SET loc_area_2_id = ll1.parent_id
            FROM area_level_1 ll1
            WHERE farmer_plot.loc_area_1_id = ll1.id
            AND farmer_plot.loc_area_2_id IS NULL;
            
            UPDATE farmer_plot
            SET loc_area_3_id = ll2.parent_id
            FROM area_level_2 ll2
            WHERE farmer_plot.loc_area_2_id = ll2.id
            AND farmer_plot.loc_area_3_id IS NULL;
        """)
    
    @api.depends('country_id')
    def _compute_loc_area_details(self):
        cll_env = self.env['country.location.level']
        for farmer in self:
            loc_details, max_level = cll_env._get_country_details(farmer.country_id.id)
            farmer.loc_area_1_label = loc_details[1]
            farmer.loc_area_2_label = loc_details[2]
            farmer.loc_area_3_label = loc_details[3]
            farmer.loc_area_4_label = loc_details[4]
            farmer.loc_area_5_label = loc_details[5]
            farmer.loc_area_6_label = loc_details[6]
            farmer.loc_area_max_level = max_level

    @api.onchange('loc_area_1_id')
    def _onchange_loc_area_1_id(self):
        if self.loc_area_1_id:
            self.loc_area_2_id = self.loc_area_1_id.parent_id

            if self.farmer_group_id and self.loc_area_1_id != self.farmer_group_id.loc_area_1_id:
                self.farmer_group_id = False

    @api.onchange('loc_area_2_id')
    def _onchange_loc_area_2_id(self):
        if self.loc_area_2_id:
            self.loc_area_3_id = self.loc_area_2_id.parent_id
        else:
            self.loc_area_3_id = False
        self.loc_area_3_id = False

    @api.onchange('loc_area_3_id')
    def _onchange_region_id(self):
        if self.loc_area_3_id:
            self.loc_area_4_id = self.loc_area_3_id.parent_id
        else:
            self.loc_area_4_id = False

        self.loc_area_2_id = False
        self.loc_area_1_id = False

    @api.onchange('loc_area_4_id')
    def _onchange_loc_area_4_id(self):
        if self.loc_area_4_id:
            self.loc_area_5_id = self.loc_area_4_id.parent_id
        else:
            self.loc_area_5_id = False

        self.loc_area_3_id = False
        self.loc_area_2_id = False
        self.loc_area_1_id = False

    @api.onchange('loc_area_5_id')
    def _onchange_loc_area_5_id(self):
        if self.loc_area_5_id:
            self.loc_area_6_id = self.loc_area_5_id.parent_id
        else:
            self.loc_area_6_id = False

        self.loc_area_4_id = False
        self.loc_area_3_id = False
        self.loc_area_2_id = False
        self.loc_area_1_id = False

    @api.onchange('loc_area_6_id')
    def _onchange_loc_area_6_id(self):
        self.loc_area_5_id = False
        self.loc_area_4_id = False
        self.loc_area_3_id = False
        self.loc_area_2_id = False
        self.loc_area_1_id = False
    
    @api.constrains('year_established')
    def _check_year_of_farm_establishment(self):
        for rec in self:
            year = rec.year_established
            
            if year:
                if not year.isdigit():
                    raise ValidationError(_("Year must be digits only!"))
                if len(year) != 4:
                    raise ValidationError(_("Year must be 4 digits!"))
    
    @api.constrains('plot_size')
    def _check_plot_size(self):
        for rec in self:
            if rec.plot_size < 0.0:
                raise ValidationError(_("Farm size of plot needs to be higher than 0."))
    
    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        
        if view_type == 'list' and view == self.env.ref('agrios.farmer_plot_tree', raise_if_not_found=False):
            company_country_id = self.env.company.country_id.id
            loc_details, max_level = self.env['country.location.level']._get_country_details(company_country_id)
            
            lev6 = arch.xpath("//field[@name='loc_area_6_id']")[0]
            if max_level >= 6:
                lev6.set('string', loc_details[6])
            else:
                lev6.getparent().remove(lev6)
            
            lev5 = arch.xpath("//field[@name='loc_area_5_id']")[0]
            if max_level >= 5:
                lev5.set('string', loc_details[5])
            else:
                lev5.getparent().remove(lev5)
            
            lev4 = arch.xpath("//field[@name='loc_area_4_id']")[0]
            if max_level >= 4:
                lev4.set('string', loc_details[4])
            else:
                lev4.getparent().remove(lev4)
            
            lev3 = arch.xpath("//field[@name='loc_area_3_id']")[0]
            if max_level >= 3:
                lev3.set('string', loc_details[3])
            else:
                lev3.getparent().remove(lev3)
            
            lev2 = arch.xpath("//field[@name='loc_area_2_id']")[0]
            if max_level >= 2:
                lev2.set('string', loc_details[2])
            else:
                lev2.getparent().remove(lev2)
            
            lev1 = arch.xpath("//field[@name='loc_area_1_id']")[0].set('string', loc_details[1])
        
        return arch, view