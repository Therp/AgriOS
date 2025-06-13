# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import ormcache
from odoo.exceptions import ValidationError


class CountryLocationLevel(models.Model):
    _name = 'country.location.level'
    _description = 'Country Location Area'
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
    parent_id = fields.Many2one('area.level.6', 'Parent Area', domain="[('country_id','=',country_id)]")
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
    parent_id = fields.Many2one('area.level.5', 'Parent Area', domain="[('country_id','=',country_id)]")
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
    

class Arealevel3(models.Model): # AreaLevel3
    _name = 'area.level.3'
    _description = 'Area Level 3'
    _order = 'country_id, name'
    
    name = fields.Char(required=True)
    manager_id = fields.Many2one('res.users', 'Area Manager')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    parent_id = fields.Many2one('area.level.4', 'Parent Area', domain="[('country_id','=',country_id)]")
    active = fields.Boolean('Active', default=True)
    is_parent_required = fields.Boolean(compute='_compute_is_parent_required', string='Parent Area Required')
    
    _sql_constraints = [
        ('unique_region_name', 'UNIQUE(name)', 'An Location Area with this name already exists!'),
    ]
    
    @api.depends('country_id')
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env['country.location.level']._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 3


class Arealevel2(models.Model): # AreaLevel2
    _name = 'area.level.2'
    _description = 'Area Level 2'
    _order = 'country_id, name'
    
    name = fields.Char(required=True)
    parent_id = fields.Many2one('area.level.3', 'Parent Area', domain="[('country_id','=',country_id)]", ondelete='restrict')
    manager_id = fields.Many2one('res.users', 'Area Manager')
    active = fields.Boolean('Active', default=True)
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    is_parent_required = fields.Boolean(compute='_compute_is_parent_required', string='Parent Area Required')
    
    _sql_constraints = [
        ('unique_loc_area_2_name', 'UNIQUE(name)','An Location Area with this name already Exists'),
    ]
    @api.constrains('country_id', 'parent_id')
    def _check_parent_required_if_country_requires_level2(self):
        cll_env = self.env['country.location.level']
        for area in self:
            loc_details, max_level = cll_env._get_country_details(area.country_id.id)
            if max_level >2 and not area.parent_id:
                raise ValidationError("Parent Area is required for countries that require Level 2 areas.")

    @api.depends('country_id')
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env['country.location.level']._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 2
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if self._context.get('filter_regions'):
            filter_region_ids = self._context['filter_regions']
            if filter_region_ids:
                if not domain: domain = []
                domain = [ ['parent_id','in',filter_region_ids] ] + domain
        
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('filter_regions'):
            filter_region_ids = self._context['filter_regions']
            if filter_region_ids:
                if not domain: domain = []
                domain = [ ['parent_id','in',filter_region_ids] ] + domain
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    

class AreaLevel1(models.Model): # AreaLevel1
    _name = 'area.level.1'
    _description = 'Area Level 1'
    _order = 'country_id, name, parent_id'
    
    name = fields.Char(required=True)
    parent_id = fields.Many2one('area.level.2', 'Parent Area', domain="[('country_id','=',country_id)]", ondelete='restrict')
    active = fields.Boolean('Active', default=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    
    farmer_group_ids = fields.One2many('farmer.group', 'loc_area_1_id', 'Farmer Groups', readonly=True, copy=False)
    manager_id = fields.Many2one('res.users', 'Area Manager')

    
    _sql_constraints = [
        ('unique_level_1_level_3_combination', 'UNIQUE(name, loc_area_2_id)', 'An Location Area with this name already Exists in the specified Location Area 2'),
    ]

    @api.constrains('country_id', 'parent_id')
    def _check_parent_required_if_country_requires_level2(self):
        cll_env = self.env['country.location.level']
        for area in self:
            loc_details, max_level = cll_env._get_country_details(area.country_id.id)
            if max_level >1 and not area.parent_id:
                raise ValidationError("Parent Area is required for countries that require Level 2 areas.")

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if self._context.get('filter_loc_area_2s'):
            filter_loc_area_2_ids = self._context['filter_loc_area_2s']
            if filter_loc_area_2_ids:
                if not domain: domain = []
                domain = [ ['loc_area_2_id','in',filter_loc_area_2_ids] ] + domain
        
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('filter_loc_area_2s'):
            filter_loc_area_2_ids = self._context['filter_loc_area_2s']
            if filter_loc_area_2_ids:
                if not domain: domain = []
                domain = [ ['loc_area_2_id','in',filter_loc_area_2_ids] ] + domain
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    

class FarmerGroup(models.Model):
    _name = 'farmer.group'
    _description = "Farmer Group"
    _order = 'name, loc_area_1_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    
    loc_area_1_id = fields.Many2one('area.level.1', string='Location Area 1', tracking=True, required=True)
    loc_area_2_id = fields.Many2one('area.level.2', 'Location Area 2', ondelete='restrict', tracking=True)
    loc_area_3_id = fields.Many2one('area.level.3', 'Location Area 3', ondelete='restrict', tracking=True)
    loc_area_4_id = fields.Many2one('area.level.4', 'Location Area 4', ondelete='restrict', tracking=True)
    loc_area_5_id = fields.Many2one('area.level.5', 'Location Area 5', ondelete='restrict', tracking=True)
    loc_area_6_id = fields.Many2one('area.level.6', 'Location Area 6', ondelete='restrict', tracking=True)
    
    loc_area_1_label = fields.Char('Location Area 1 Label', compute="_compute_loc_area_details")
    loc_area_2_label = fields.Char('Location Area 2 Label', compute="_compute_loc_area_details")
    loc_area_3_label = fields.Char('Location Area 3 Label', compute="_compute_loc_area_details")
    loc_area_4_label = fields.Char('Location Area 4 Label', compute="_compute_loc_area_details")
    loc_area_5_label = fields.Char('Location Area 5 Label', compute="_compute_loc_area_details")
    loc_area_6_label = fields.Char('Location Area 6 Label', compute="_compute_loc_area_details")
    loc_area_max_level = fields.Integer('Max Location Area', compute="_compute_loc_area_details")
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=lambda self: self.env.company.country_id)
    manager_id = fields.Many2one(related='loc_area_1_id.manager_id')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
    
    chairperson_id = fields.Many2one('res.partner', tracking=True, domain="[('is_farmer','=',True),('farmer_group_id','=',id),('farmer_stage','=','verified')]")
    group_sec_id = fields.Many2one('res.partner', 'Secretary', tracking=True, domain="[('is_farmer','=', True),('farmer_group_id','=',id),('farmer_stage','=','verified')]")
    group_treasurer_id = fields.Many2one('res.partner', 'Treasurer', tracking=True, domain="[('is_farmer','=',True),('farmer_group_id','=',id),('farmer_stage','=','verified')]")
    member_ids = fields.One2many('res.partner', 'farmer_group_id', domain=[('is_farmer','=',True),('farmer_stage','=','verified')])
    
    total_due = fields.Monetary('Group Amount Due', compute='_compute_total_due', help="Sum amount due of all the group members")
    
    _sql_constraints = [
        ('unique_group_loc_area_1_combination', 'UNIQUE(name, loc_area_1_id)', 'A Group with this name already Exists in the specified Location Area 1')
    ]
    
    def init(self):
        super().init()
        self._cr.execute("""
            UPDATE farmer_group
            SET loc_area_2_id = ll1.parent_id
            FROM area_level_1 ll1
            WHERE farmer_group.loc_area_1_id = ll1.id
            AND farmer_group.loc_area_2_id IS NULL;
            
            UPDATE farmer_group
            SET loc_area_3_id = ll2.parent_id
            FROM area_level_2 ll2
            WHERE farmer_group.loc_area_2_id = ll2.id
            AND farmer_group.loc_area_2_id IS NULL;
        """)
    
    @api.depends('member_ids')
    def _compute_total_due(self):
        for farm_group in self:
            farm_group.total_due = 0.0
            for member in farm_group.member_ids:
                for aml in member.unreconciled_aml_ids:
                    if aml.company_id == farm_group.company_id and not aml.blocked:
                        farm_group.total_due += aml.amount_residual
    
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
    
    @api.onchange('loc_area_2_id')
    def _onchange_loc_area_2_id(self):
        if self.loc_area_2_id:
            self.loc_area_3_id = self.loc_area_2_id.parent_id
            
            if self.loc_area_1_id and self.loc_area_1_id.parent_id != self.loc_area_2_id:
                self.loc_area_1_id = False
    
    @api.onchange('loc_area_3_id')
    def _onchange_region_id(self):
        if self.loc_area_3_id:
            self.loc_area_4_id = self.loc_area_3_id.parent_id
            
            if self.loc_area_2_id and self.loc_area_2_id.parent_id != self.loc_area_3_id:
                self.loc_area_2_id = False
                self.loc_area_1_id = False
    
    @api.onchange('loc_area_4_id')
    def _onchange_loc_area_4_id(self):
        if self.loc_area_4_id:
            self.loc_area_5_id = self.loc_area_4_id.parent_id
            
            if self.loc_area_3_id and self.loc_area_3_id.parent_id != self.loc_area_4_id:
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False
    
    @api.onchange('loc_area_5_id')
    def _onchange_loc_area_5_id(self):
        if self.loc_area_5_id:
            self.loc_area_6_id = self.loc_area_5_id.parent_id
            
            if self.loc_area_4_id and self.loc_area_4_id.parent_id != self.loc_area_5_id:
                self.loc_area_4_id = False
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False
    
    @api.onchange('loc_area_6_id')
    def _onchange_loc_area_6_id(self):
        if self.loc_area_6_id:
            if self.loc_area_5_id and self.loc_area_5_id.parent_id != self.loc_area_6_id:
                self.loc_area_5_id = False
                self.loc_area_4_id = False
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False
    
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
    