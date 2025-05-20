# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import ormcache


class CountryLocationLevel(models.Model):
    _name = 'country.location.level'
    _description = 'Country Area Level'
    _order = 'country_id, level'
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    level = fields.Integer('Level', required=True, default=1)
    name = fields.Char('Designation', required=True)
    
    _sql_constraints = [
        ('unique_country_level', 'UNIQUE(country_id, level)', 'Country / level must be unique!'),
        ('unique_country_name', 'UNIQUE(country_id, name)', 'Country / level designation must be unique!'),
        ("check_level_value", "CHECK(level > 0 AND level < 7)", "Level needs to be between 1 and 6!"),
    ]
    
    @ormcache('country_id')
    def _get_country_details(self, country_id):
        if country_id:
            self._cr.execute("SELECT level, name FROM country_location_level WHERE country_id = %s", (country_id,))
            loc_details = dict(self._cr.fetchall())
        else:
            loc_details = {}
        
        max_level = 1
        
        for level in range(1, 7):
            if level not in loc_details:
                loc_details[level] = '- Undefined -' if level != 1 else 'Village'
            elif level > max_level:
                max_level = level
        
        return loc_details, max_level
    
    @api.model_create_multi
    def create(self, vals_list):
        ret = super().create(vals_list)
        self.env.registry.clear_cache()
        return ret
    
    def write(self, vals):
        ret = super().write(vals)
        self.env.registry.clear_cache()
        return ret
    
    def unlink(self):
        ret = super().unlink()
        self.env.registry.clear_cache()
        return ret
    

class AreaLevel6(models.Model):
    _name = 'area.level.6'
    _description = 'Area Level 6'
    _order = 'country_id, name'
    
    name = fields.Char('Name', required=True)
    manager_id = fields.Many2one('res.users', 'Area Manager')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'An area 6 with the same name already exists!'),
    ]
    

class AreaLevel5(models.Model):
    _name = 'area.level.5'
    _description = 'Area Level 5'
    _order = 'country_id, name'
    
    name = fields.Char('Name', required=True)
    manager_id = fields.Many2one('res.users', 'Area Manager')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    parent_id = fields.Many2one('area.level.6', 'Parent Area')
    active = fields.Boolean('Active', default=True)
    is_parent_required = fields.Boolean(compute='_compute_is_parent_required', string='Parent Area Required')
    
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'An area 5 with the same name already exists!'),
    ]
    
    @api.depends('country_id')
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env['country.location.level']._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 5
    

class AreaLevel4(models.Model):
    _name = 'area.level.4'
    _description = 'Area Level 4'
    _order = 'country_id, name'
    
    name = fields.Char('Name', required=True)
    manager_id = fields.Many2one('res.users', 'Area Manager')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    parent_id = fields.Many2one('area.level.5', 'Parent Area')
    active = fields.Boolean('Active', default=True)
    is_parent_required = fields.Boolean(compute='_compute_is_parent_required', string='Parent Area Required')
    
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'An area 4 with the same name already exists!'),
    ]
    
    @api.depends('country_id')
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env['country.location.level']._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 4
    

class Region(models.Model): # AreaLevel3
    _name = 'area.level.3'
    _description = 'Area Level 3'
    _order = 'country_id, name'
    
    name = fields.Char(required=True)
    manager_id = fields.Many2one('res.users', 'Area Manager')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    parent_id = fields.Many2one('area.level.4', 'Parent Area')
    active = fields.Boolean('Active', default=True)
    is_parent_required = fields.Boolean(compute='_compute_is_parent_required', string='Parent Area Required')
    
    _sql_constraints = [
        ('unique_region_name', 'UNIQUE(name)', 'An Area level with this name already exists!'),
    ]
    
    @api.depends('country_id')
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env['country.location.level']._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 3


class District(models.Model): # AreaLevel2
    _name = 'district'
    _description = 'Administrative District'
    _order = 'country_id, name'
    
    name = fields.Char(required=True)
    area_level_3_id = fields.Many2one('area.level.3', 'Region', required=True, ondelete='restrict')
    district_manager_id = fields.Many2one('res.users', 'Area Manager')
    active = fields.Boolean('Active', default=True)
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    
    _sql_constraints = [
        ('unique_district_name', 'UNIQUE(name)','An Area level with this name already Exists'),
    ]
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if self._context.get('filter_regions'):
            filter_region_ids = self._context['filter_regions']
            if filter_region_ids:
                if not domain: domain = []
                domain = [ ['area_level_3_id','in',filter_region_ids] ] + domain
        
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('filter_regions'):
            filter_region_ids = self._context['filter_regions']
            if filter_region_ids:
                if not domain: domain = []
                domain = [ ['area_level_3_id','in',filter_region_ids] ] + domain
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    

class Cooperative(models.Model): # AreaLevel1
    _name = 'cooperative'
    _description = 'Cooperative, Community or Cluster Group'
    _order = 'country_id, name, district_id'
    
    name = fields.Char(required=True)
    district_id = fields.Many2one('district', 'District', required=True, ondelete='restrict')
    active = fields.Boolean('Active', default=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    
    farmer_group_ids = fields.One2many('farmer.group', 'coop_id', 'Farmer Groups', readonly=True, copy=False)
    community_facilitator_id = fields.Many2one('res.users', 'Community Facilitator')
    area_level_3_id = fields.Many2one(string='Region', related='district_id.area_level_3_id')
    
    _sql_constraints = [
        ('unique_coop_region_combination', 'UNIQUE(name, district_id)', 'An Area level with this name already Exists in the specified District'),
    ]
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if self._context.get('filter_districts'):
            filter_district_ids = self._context['filter_districts']
            if filter_district_ids:
                if not domain: domain = []
                domain = [ ['district_id','in',filter_district_ids] ] + domain
        
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('filter_districts'):
            filter_district_ids = self._context['filter_districts']
            if filter_district_ids:
                if not domain: domain = []
                domain = [ ['district_id','in',filter_district_ids] ] + domain
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    

class FarmerGroup(models.Model):
    _name = 'farmer.group'
    _description = "Farmers' Group"
    _order = 'name, coop_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    
    coop_id = fields.Many2one('cooperative', string='Location Area 1', tracking=True, required=True)
    district_id = fields.Many2one('district', 'Location Area 2', ondelete='restrict', tracking=True)
    area_level_3_id = fields.Many2one('area.level.3', 'Location Area 3', ondelete='restrict', tracking=True)
    loc_area_4_id = fields.Many2one('area.level.4', 'Location Area 4', ondelete='restrict', tracking=True)
    loc_area_5_id = fields.Many2one('area.level.5', 'Location Area 5', ondelete='restrict', tracking=True)
    loc_area_6_id = fields.Many2one('area.level.6', 'Location Area 6', ondelete='restrict', tracking=True)
    
    loc_area_1_label = fields.Char('Location Area 1 Label', compute="_compute_loc_area_details")
    loc_area_2_label = fields.Char('Location Area 2 Label', compute="_compute_loc_area_details")
    loc_area_3_label = fields.Char('Location Area 3 Label', compute="_compute_loc_area_details")
    loc_area_4_label = fields.Char('Location Area 4 Label', compute="_compute_loc_area_details")
    loc_area_5_label = fields.Char('Location Area 5 Label', compute="_compute_loc_area_details")
    loc_area_6_label = fields.Char('Location Area 6 Label', compute="_compute_loc_area_details")
    loc_area_max_level = fields.Integer('Max Location Area Level', compute="_compute_loc_area_details")
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    community_facilitator_id = fields.Many2one(related='coop_id.community_facilitator_id')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
    
    chairperson_id = fields.Many2one('res.partner', tracking=True, domain="[('is_outgrower','=',True),('farmer_group_id','=',id),('outgrower_stage','=','verified')]")
    group_sec_id = fields.Many2one('res.partner', 'Secretary', tracking=True, domain="[('is_outgrower','=', True),('farmer_group_id','=',id),('outgrower_stage','=','verified')]")
    group_treasurer_id = fields.Many2one('res.partner', 'Treasurer', tracking=True, domain="[('is_outgrower','=',True),('farmer_group_id','=',id),('outgrower_stage','=','verified')]")
    member_ids = fields.One2many('res.partner', 'farmer_group_id', domain=[('is_outgrower','=',True),('outgrower_stage','=','verified')])
    
    total_due = fields.Monetary('Group Amount Due', compute='_compute_total_due', help="Sum amount due of all the group members")
    
    _sql_constraints = [
        ('unique_group_coop_combination', 'UNIQUE(name, coop_id)', 'A Group with this name already Exists in the specified Coop/Cluster')
    ]
    
    def init(self):
        super().init()
        self._cr.execute("""
            UPDATE farmer_group
            SET district_id = ll1.district_id
            FROM cooperative ll1
            WHERE farmer_group.coop_id = ll1.id
            AND farmer_group.district_id IS NULL;
            
            UPDATE farmer_group
            SET area_level_3_id = ll2.area_level_3_id
            FROM district ll2
            WHERE farmer_group.district_id = ll2.id
            AND farmer_group.area_level_3_id IS NULL;
        """)
    
    @api.depends('member_ids')
    def _compute_total_due(self):
        for farm_group in self:
            farm_group.total_due = 0.0
            for member in farm_group.member_ids:
                for aml in member.agrios_unreconciled_aml_ids:
                    if aml.company_id == farm_group.company_id and not aml.blocked:
                        farm_group.total_due += aml.amount_residual
    
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
            self.area_level_3_id = self.district_id.area_level_3_id
            
            if self.coop_id and self.coop_id.district_id != self.district_id:
                self.coop_id = False
    
    @api.onchange('area_level_3_id')
    def _onchange_region_id(self):
        if self.area_level_3_id:
            self.loc_area_4_id = self.area_level_3_id.parent_id
            
            if self.district_id and self.district_id.area_level_3_id != self.area_level_3_id:
                self.district_id = False
                self.coop_id = False
    
    @api.onchange('loc_area_4_id')
    def _onchange_loc_area_4_id(self):
        if self.loc_area_4_id:
            self.loc_area_5_id = self.loc_area_4_id.parent_id
            
            if self.area_level_3_id and self.area_level_3_id.parent_id != self.loc_area_4_id:
                self.area_level_3_id = False
                self.district_id = False
                self.coop_id = False
    
    @api.onchange('loc_area_5_id')
    def _onchange_loc_area_5_id(self):
        if self.loc_area_5_id:
            self.loc_area_6_id = self.loc_area_5_id.parent_id
            
            if self.loc_area_4_id and self.loc_area_4_id.parent_id != self.loc_area_5_id:
                self.loc_area_4_id = False
                self.area_level_3_id = False
                self.district_id = False
                self.coop_id = False
    
    @api.onchange('loc_area_6_id')
    def _onchange_loc_area_6_id(self):
        if self.loc_area_6_id:
            if self.loc_area_5_id and self.loc_area_5_id.parent_id != self.loc_area_6_id:
                self.loc_area_5_id = False
                self.loc_area_4_id = False
                self.area_level_3_id = False
                self.district_id = False
                self.coop_id = False
    
    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        
        if view_type == 'list' and view == self.env.ref('agrios.view_farmer_group_tree', raise_if_not_found=False):
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
            
            lev3 = arch.xpath("//field[@name='area_level_3_id']")[0]
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
    