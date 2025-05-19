# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartnerArea(models.Model):
    _name = 'res.partner.area'
    _inherit = ["mail.thread"]
    _description = 'Outgrower Farm Plot'
    _order = 'partner_id'
    
    def _get_farm_uom_domain(self):
        surface_uom = self.env.ref('uom.uom_categ_surface', raise_if_not_found=False).id
        return [('category_id.id', '=', surface_uom),('uom_type', '=', 'bigger')]
    
    def _get_default_farm_uom(self):
        farm_uom_config = self.env['ir.config_parameter'].sudo().get_param('outgrower_management.farm_uom')
        return farm_uom_config and int(farm_uom_config) or self.env.ref('ai_oms.area_1', raise_if_not_found=False)
    
    name = fields.Char('Name', required=True, tracking=True)
    
    gshape_name = fields.Char('Gshape Name')
    gshape_type = fields.Selection([('circle', 'Circle'),('polygon', 'Polygon'),('rectangle', 'Rectangle')], 'Plot Shape Type')
    gshape_description = fields.Text('Description')
    
    partner_id = fields.Many2one('res.partner', 'Outgrower', domain="[('is_outgrower','=',True)]", required=True, ondelete='cascade', tracking=True, index=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    year_of_farm_establishment = fields.Char('Year of Farm Establishment', tracking=True)
    registration_year = fields.Integer('Year of Registration')
    is_owner = fields.Boolean('Owned By Outgrower', help='If the outgrower owns the plot of land or not', default=True)
    farm_in_protected_area = fields.Boolean('Farm in Protected Area')
    farm_uom_id = fields.Many2one('uom.uom', 'Farm UOM', domain=_get_farm_uom_domain, default=_get_default_farm_uom, tracking=True, readonly=True)
    farm_size = fields.Float('Farm Area', required=True, tracking=True)
    farm_condition = fields.Selection([('bad', 'Bad'),('needsimprovement','Needs Improvement'),('good','Good'),('verygood','Very Good')], default=False)
    intercropping = fields.Boolean('Intercropping')
    subplot_ids = fields.One2many('res.partner.subplot', 'plot_id', string='Subplots')
    
    coop_id = fields.Many2one('cooperative', 'Location Area 1', tracking=True)
    district_id = fields.Many2one('district', 'Location Area 2', ondelete='restrict', tracking=True)
    region_id = fields.Many2one('region', 'Location Area 3', ondelete='restrict', tracking=True)
    loc_area_4_id = fields.Many2one('area.level.4', 'Location Area 4', ondelete='restrict', tracking=True)
    loc_area_5_id = fields.Many2one('area.level.5', 'Location Area 5', ondelete='restrict', tracking=True)
    loc_area_6_id = fields.Many2one('area.level.6', 'Location Area 6', ondelete='restrict', tracking=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    
    loc_area_1_label = fields.Char('Location Area 1 Label', compute="_compute_loc_area_details")
    loc_area_2_label = fields.Char('Location Area 2 Label', compute="_compute_loc_area_details")
    loc_area_3_label = fields.Char('Location Area 3 Label', compute="_compute_loc_area_details")
    loc_area_4_label = fields.Char('Location Area 4 Label', compute="_compute_loc_area_details")
    loc_area_5_label = fields.Char('Location Area 5 Label', compute="_compute_loc_area_details")
    loc_area_6_label = fields.Char('Location Area 6 Label', compute="_compute_loc_area_details")
    loc_area_max_level = fields.Integer('Max Location Area Level', compute="_compute_loc_area_details")
    
    main_road = fields.Char('Main Road')
    main_road_distance = fields.Float('Main Road Distance (km)')
    gps_location = fields.Char('GPS Location', tracking=True)
    
    plot_polygon = fields.Json('Plot Area')
    country_code = fields.Char(compute='_compute_country_code', default=lambda self: self.env.company.country_id.code or False)
    
    def _compute_country_code(self):
        country_code = self.env.company.country_id.code or False
        for rpa in self:
            rpa.country_code = country_code
    
    def init(self):
        super().init()
        self._cr.execute("""
            UPDATE res_partner_area
            SET district_id = ll1.district_id
            FROM cooperative ll1
            WHERE res_partner_area.coop_id = ll1.id
            AND res_partner_area.district_id IS NULL;
            
            UPDATE res_partner_area
            SET region_id = ll2.region_id
            FROM district ll2
            WHERE res_partner_area.district_id = ll2.id
            AND res_partner_area.region_id IS NULL;
        """)
    
    @api.depends('country_id')
    def _compute_loc_area_details(self):
        cll_env = self.env['country.location.level']
        for outgrower in self:
            loc_details, max_level = cll_env._get_country_details(outgrower.country_id.id)
            outgrower.loc_area_1_label = loc_details[1]
            outgrower.loc_area_2_label = loc_details[2]
            outgrower.loc_area_3_label = loc_details[3]
            outgrower.loc_area_4_label = loc_details[4]
            outgrower.loc_area_5_label = loc_details[5]
            outgrower.loc_area_6_label = loc_details[6]
            outgrower.loc_area_max_level = max_level
    
    @api.onchange('coop_id')
    def _onchange_coop_id(self):
        if self.coop_id:
            self.district_id = self.coop_id.district_id
    
    @api.onchange('district_id')
    def _onchange_district_id(self):
        if self.district_id:
            self.region_id = self.district_id.region_id
            
            if self.coop_id and self.coop_id.district_id != self.district_id:
                self.coop_id = False
    
    @api.onchange('region_id')
    def _onchange_region_id(self):
        if self.region_id:
            self.loc_area_4_id = self.region_id.parent_id
            
            if self.district_id and self.district_id.region_id != self.region_id:
                self.district_id = False
    
    @api.onchange('loc_area_4_id')
    def _onchange_loc_area_4_id(self):
        if self.loc_area_4_id:
            self.loc_area_5_id = self.loc_area_4_id.parent_id
            
            if self.region_id and self.region_id.parent_id != self.loc_area_4_id:
                self.region_id = False
    
    @api.onchange('loc_area_5_id')
    def _onchange_loc_area_5_id(self):
        if self.loc_area_5_id:
            self.loc_area_6_id = self.loc_area_5_id.parent_id
            
            if self.loc_area_4_id and self.loc_area_4_id.parent_id != self.loc_area_5_id:
                self.loc_area_4_id = False
    
    @api.onchange('loc_area_6_id')
    def _onchange_loc_area_6_id(self):
        if self.loc_area_6_id:
            if self.loc_area_5_id and self.loc_area_5_id.parent_id != self.loc_area_6_id:
                self.loc_area_5_id = False
    
    @api.constrains('year_of_farm_establishment')
    def _check_year_of_farm_establishment(self):
        for rec in self:
            year = rec.year_of_farm_establishment
            
            if year:
                if not year.isdigit():
                    raise ValidationError(_("Year must be digits only!"))
                if len(year) != 4:
                    raise ValidationError(_("Year must be 4 digits!"))
    
    @api.constrains('farm_size')
    def _check_farm_size(self):
        for rec in self:
            if rec.farm_size < 0.0:
                raise ValidationError(_("Farm size of plot needs to be higher than 0."))
    
    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        
        if view_type == 'list' and view == self.env.ref('ai_oms.res_partner_area_tree', raise_if_not_found=False):
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
            
            lev3 = arch.xpath("//field[@name='region_id']")[0]
            if max_level >= 3:
                lev3.set('string', loc_details[3])
            else:
                lev3.getparent().remove(lev3)
            
            lev2 = arch.xpath("//field[@name='district_id']")[0]
            if max_level >= 2:
                lev2.set('string', loc_details[2])
            else:
                lev2.getparent().remove(lev2)
            
            lev1 = arch.xpath("//field[@name='coop_id']")[0].set('string', loc_details[1])
        
        return arch, view