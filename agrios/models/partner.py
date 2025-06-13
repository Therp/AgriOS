# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from collections import defaultdict


class Farmer(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'phone', 'farmer_ref']
    
    @api.model
    def _get_land_area_uom_domain(self):
        return [('category_id.id', '=', self.env.ref('uom.uom_categ_surface').id), ('uom_type','=','bigger')]
    
    @api.model
    def _default_land_area_uom(self):
        land_area_uom = int(self.env['ir.config_parameter'].sudo().get_param('farmer_management.land_area_uom') or 0)
        if not land_area_uom:
            land_area_uom = self.env.ref('agrios.area_1', raise_if_not_found=False)
        return land_area_uom
    
    is_farmer = fields.Boolean('Farmer', default=False)
    is_farmer_trainer = fields.Boolean('Farmer Trainer', default=False)
    farmer_requires_contract = fields.Boolean('Requires Contract', tracking=True, default=False, help="If selected, this farmer will require a valid offtake agreement contract to sell inputs or to buy off-takes. If unselected, no valid contract is needed for sales or purchases.")
    
    farmer_ref = fields.Char('Farmer Reference', default='/', readonly=True, copy=False)
    
    farmer_group_id = fields.Many2one('farmer.group', 'Farmer Group', domain="[('loc_area_1_id', '=?', loc_area_1_id)]", tracking=True)
    loc_area_1_id = fields.Many2one('area.level.1', 'Location Area 1', ondelete='restrict', tracking=True)
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
    
    manager_id = fields.Many2one(related='loc_area_1_id.manager_id')
    
    # Basic farmer details
    gender = fields.Selection([('female', 'Female'), ('male', 'Male')], string='Gender')
    farmer_id_number = fields.Char(string='ID Number', tracking=True)
    birthday = fields.Date(string='Date of Birth')
    age = fields.Integer(compute='_compute_age')
    farmer_stage = fields.Selection([('draft', 'Draft'),('verified', 'Verified')], 'Farmer Stage', default='draft', copy=False)
    
    # farm details
    own_acreage = fields.Float('Own Plot Acreage', compute='_compute_land_acreage', inverse='_inverse_farm_acreage', store=True, tracking=True)
    leased_acreage = fields.Float('Leased Plot Acreage', compute='_compute_land_acreage', inverse='_inverse_leased_acreage', store=True, tracking=True)
    total_acreage = fields.Float('Total Plot Acreage', compute='_compute_total_acreage', store=True)
    total_contracted_acreage = fields.Float('Total Contracted Acreage', compute='_compute_total_contracted_acreage')
    non_contracted_acreage = fields.Float('Non-Contracted Acreage', compute='_compute_non_contracted_acreage')
    
    plot_ids = fields.One2many('farmer.plot', 'partner_id', 'Responsible Area', copy=False)
    
    # Linked Offtake Agreements
    count_farmer_contracts = fields.Integer(compute='_compute_count_farmer_contracts')
    farmer_contract_ids = fields.One2many('farmer.contract', 'farmer_id', 'Contracts')
    
    open_contract_ids = fields.One2many('farmer.contract', string='Open Contracts', compute='_compute_open_contracts')
    open_contract_input_ids = fields.One2many('farmer.contract', string='Open Contracts [Input State]', compute='_compute_open_contracts')
    open_contract_harvest_ids = fields.One2many('farmer.contract', string='Open Contracts [Harvest State]', compute='_compute_open_contracts')
    
    count_input_sales = fields.Integer(compute='_compute_count_input_sales')
    count_harvest_offtakes = fields.Integer(compute='_compute_count_harvest_offtakes')
    count_trainings = fields.Integer(compute='_compute_count_trainings')
    
    certification_ids = fields.One2many('farmer.certification', 'farmer_id')
    
    training_ids = fields.Many2many('farmer.training', domain=[('training_state', '=', 'done')])
    
    crop_product_ids = fields.Many2many('product.product', 'res_partner_product_harvest_crops_rel', 'partner_id', 'product_id', domain=[('crop_product','=',True)], string="Crop Products")
    
    land_area_uom = fields.Many2one('uom.uom', 'Land Area Unit of Measure', domain=lambda self: self._get_land_area_uom_domain(), default=lambda self: self._default_land_area_uom(), tracking=True)
    
    # extra farmer info
    family_size = fields.Integer()
    next_of_kin = fields.Char()
    nok_id = fields.Char(string='NOK ID')
    nok_phone = fields.Char(string='NOK Phone')
    
    count_certifications = fields.Integer('Valid Certifications', compute='_compute_certifications', help="Number of valid certifications")
    certified = fields.Boolean('Currently Certified', compute='_compute_certifications', search='_search_certified')
    
    has_expired_contract = fields.Boolean(compute='_compute_has_expired_contract')
    
    can_order_inputs = fields.Boolean('Can Order Inputs [Without Confirmation]', compute='_compute_can_order_inputs')
    can_order_inputs_confirm = fields.Boolean('Can Order Inputs [With Confirmation]', compute='_compute_can_order_inputs')
    
    can_register_offtakes = fields.Boolean('Can Register Offtakes [Without Confirmation]', compute='_compute_can_register_offtakes')
    can_register_offtakes_confirm = fields.Boolean('Can Register Offtakes [With Confirmation]', compute='_compute_can_register_offtakes')
    
    country_id = fields.Many2one(required=True, default=lambda self: self.env.company.country_id)
    interactions_count = fields.Integer(compute='_compute_interactions_count', string='Interactions')
    
    unreconciled_aml_ids = fields.One2many('account.move.line', compute='_compute_agrios_unreconciled_aml_ids', readonly=False) # copy of enterprise unreconciled_aml_ids
    
    @api.depends('invoice_ids')
    @api.depends_context('company', 'allowed_company_ids')
    def _compute_agrios_unreconciled_aml_ids(self):
        if not self: return
        
        if hasattr(self[0], 'unreconciled_aml_ids'):
            for ptn in self:
                ptn.unreconciled_aml_ids = ptn.unreconciled_aml_ids
        
        else:
            unreconciled_aml_ids = defaultdict(list)
            for overdue, partner, amount_residual_sum, aml_ids in self.env['account.move.line']._read_group(
                domain=self._get_unreconciled_aml_domain(),
                groupby=['followup_overdue', 'partner_id'],
                aggregates=['amount_residual:sum', 'id:array_agg'],
            ):
                unreconciled_aml_ids[partner] += aml_ids
                due_data[partner] += amount_residual_sum
                if overdue:
                    overdue_data[partner] += amount_residual_sum
                
            for partner in self:
                partner.unreconciled_aml_ids = self.env['account.move.line'].browse(unreconciled_aml_ids.get(partner, []))
    
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
    
    @api.depends('plot_ids', 'plot_ids.plot_size')
    def _compute_land_acreage(self):
        for farmer in self:
            if farmer.plot_ids:
                farmer.own_acreage = sum(farmer.plot_ids.filtered(lambda plot: plot.is_owner).mapped('plot_size'))
                farmer.leased_acreage = sum(farmer.plot_ids.filtered(lambda plot: not plot.is_owner).mapped('plot_size'))
            else:
                farmer.own_acreage = farmer.leased_acreage = 0.0
    
    def _inverse_farm_acreage(self):
        """Allows manual updates to farm_acreage via import"""
        for record in self:
            record.own_acreage = record.own_acreage
    
    def _inverse_leased_acreage(self):
        """Allows manual updates to leased_acreage via import"""
        for record in self:
            record.leased_acreage = record.leased_acreage

    @api.depends('own_acreage', 'leased_acreage')
    def _compute_total_acreage(self):
        for rec in self:
            rec.total_acreage = rec.own_acreage + rec.leased_acreage
    
    @api.depends('farmer_stage', 'farmer_requires_contract', 'company_id')
    def _compute_can_order_inputs(self):
        for farmer in self:
            if farmer.farmer_stage == 'verified':
                if farmer.open_contract_input_ids:
                    farmer.can_order_inputs = True
                    farmer.can_order_inputs_confirm = False
                elif farmer.open_contract_harvest_ids:
                    farmer.can_order_inputs_confirm = (farmer.company_id or self.env.company).allow_operations_out_of_phase
                    farmer.can_order_inputs = not farmer.can_order_inputs_confirm and not farmer.farmer_requires_contract
                else:
                    farmer.can_order_inputs = not farmer.farmer_requires_contract
                    farmer.can_order_inputs_confirm = False
            else:
                farmer.can_order_inputs = farmer.can_order_inputs_confirm = False
    
    @api.depends('farmer_stage', 'farmer_requires_contract', 'company_id')
    def _compute_can_register_offtakes(self):
        for farmer in self:
            if farmer.farmer_stage == 'verified':
                if farmer.open_contract_harvest_ids:
                    farmer.can_register_offtakes = True
                    farmer.can_register_offtakes_confirm = False
                elif farmer.open_contract_input_ids:
                    farmer.can_register_offtakes_confirm = (farmer.company_id or self.env.company).allow_operations_out_of_phase
                    farmer.can_register_offtakes = not farmer.can_register_offtakes_confirm and not farmer.farmer_requires_contract
                else:
                    farmer.can_register_offtakes = not farmer.farmer_requires_contract
                    farmer.can_register_offtakes_confirm = False
            else:
                farmer.can_register_offtakes = farmer.can_register_offtakes_confirm = False
    
    def _compute_has_expired_contract(self):
        for farmer in self:
            farmer.has_expired_contract = any(farmer.farmer_contract_ids.mapped('expired_contract'))
    
    def _compute_open_contracts(self):
        for farmer in self:
            farmer.open_contract_ids = farmer.farmer_contract_ids.filtered(lambda cont: cont.contract_stage == 'open')
            farmer.open_contract_input_ids = farmer.open_contract_ids.filtered(lambda cont: not cont.ready_for_harvest)
            farmer.open_contract_harvest_ids = farmer.open_contract_ids.filtered(lambda cont: cont.ready_for_harvest)
    
    def _compute_count_farmer_contracts(self):
        for rec in self:
            rec.count_farmer_contracts = self.env['farmer.contract'].search_count([('farmer_id', '=', rec.id)])
    
    def _compute_count_input_sales(self):
        for rec in self:
            rec.count_input_sales = self.env['sale.order'].search_count([('partner_id', '=', rec.id)])
    
    def _compute_count_harvest_offtakes(self):
        for rec in self:
            rec.count_harvest_offtakes = self.env['purchase.order'].search_count([('partner_id', '=', rec.id)])
    
    def _compute_count_trainings(self):
        for rec in self:
            rec.count_trainings = self.env['farmer.contract'].search_count([('farmer_id', '=', rec.id)])
    
    @api.depends('certification_ids.cert_end_date')
    def _compute_certifications(self):
        today = fields.Date.today()
        
        for rec in self.sudo():
            rec.count_certifications = self.env['farmer.certification'].search_count([
                ('farmer_id','=',rec.id), ('cert_end_date','>=',today),
                ('cert_start_date','<=',today), ('force_expired','=',False),
                ('posted','=',True),
            ])
            if rec.count_certifications:
                rec.certified = True
            else:
                rec.certified = False
    
    def _compute_total_contracted_acreage(self):
        for partner in self:
            partner.total_contracted_acreage = sum(partner.farmer_contract_ids.filtered(lambda contract: contract.contract_stage == 'open').mapped('contract_acreage'))
    
    def _compute_non_contracted_acreage(self):
        for rec in self:
            rec.non_contracted_acreage = rec.total_acreage - rec.total_contracted_acreage
    
    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            if record.birthday:
                today = datetime.today()
                # Check if the date has passed this year
                if today.strftime("%m%d") >= record.birthday.strftime("%m%d"):
                    record['age'] = today.year - record.birthday.year
                else:
                    record['age'] = today.year - record.birthday.year - 1
            else:
                record['age'] = 0
        
    @api.depends('farmer_ref')
    def _compute_display_name(self):
        ret = super()._compute_display_name()
        
        for partner in self:
            if partner.farmer_ref and partner.farmer_ref != '/':
                partner.display_name = f"[{partner.farmer_ref}] {partner.display_name or ''}"
        
        return ret
        
    def _compute_interactions_count(self):
        for partner in self:
            partner.interactions_count = self.env['farmer.interaction'].search_count([('farmer_id', '=', partner.id)])
    
    def _search_certified(self, operator, value):
        if (operator == '=' and not value) or (operator == '!=' and value):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        
        self._cr.execute("""
            SELECT DISTINCT farmer_id
            FROM farmer_certification
            WHERE posted = True
              AND force_expired = FALSE
              AND cert_start_date <= CURRENT_DATE
              AND cert_end_date >= CURRENT_DATE
          """)
        return [('id', domain_operator, [r[0] for r in self._cr.fetchall()])]
    
    @api.onchange('farmer_group_id')
    def _onchange_farmer_group(self):
        if self.farmer_group_id.loc_area_1_id:
            self.loc_area_1_id = self.farmer_group_id.loc_area_1_id
    
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
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if self._context.get('filter_duplicate_identification'):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id AND ptn1.farmer_id_number = ptn2.farmer_id_number
                WHERE ptn1.farmer_id_number IS NOT NULL
            """)
            ident_duplicate_ids = [ptn[0] for ptn in self._cr.fetchall()]
            if domain:
                domain = ['&', ('id', 'in', ident_duplicate_ids)] + domain
            else:
                domain = [('id', 'in', ident_duplicate_ids)]
        
        if self._context.get('filter_duplicate_phone'):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id AND ptn1.phone = ptn2.phone
                WHERE ptn1.phone IS NOT NULL
            """)
            phone_duplicate_ids = [ptn[0] for ptn in self._cr.fetchall()]
            if domain:
                domain = ['&', ('id', 'in', phone_duplicate_ids)] + domain
            else:
                domain = [('id', 'in', phone_duplicate_ids)]
        
        return super().web_search_read(domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit)
    
    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        
        if view_type == 'search' and view == self.env.ref('agrios.view_farmer_search_filter', raise_if_not_found=False):
            company_country_id = self.env.company.country_id.id
            loc_details, max_level = self.env['country.location.level']._get_country_details(company_country_id)
            
            lev6 = arch.xpath("//filter[@name='groupby_loc_area_6_id']")[0]
            if max_level >= 6:
                lev6.set('string', loc_details[6])
            else:
                lev6.getparent().remove(lev6)
            
            lev5 = arch.xpath("//filter[@name='groupby_loc_area_5_id']")[0]
            if max_level >= 5:
                lev5.set('string', loc_details[5])
            else:
                lev5.getparent().remove(lev5)
            
            lev4 = arch.xpath("//filter[@name='groupby_loc_area_4_id']")[0]
            if max_level >= 4:
                lev4.set('string', loc_details[4])
            else:
                lev4.getparent().remove(lev4)
            
            lev3 = arch.xpath("//filter[@name='groupby_loc_area_3_id']")[0]
            if max_level >= 3:
                lev3.set('string', loc_details[3])
            else:
                lev3.getparent().remove(lev3)
            
            lev2 = arch.xpath("//filter[@name='groupby_loc_area_2_id']")[0]
            if max_level >= 2:
                lev2.set('string', loc_details[2])
            else:
                lev2.getparent().remove(lev2)
            
            lev1 = arch.xpath("//filter[@name='groupby_loc_area_1_id']")[0].set('string', loc_details[1])
        
        elif view_type == 'list' and view == self.env.ref('agrios.view_farmer_tree', raise_if_not_found=False):
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
    
    def verify_farmer(self):
        for farmer in self:
            vals = {
                'farmer_stage': 'verified',
                'farmer_requires_contract': (farmer.company_id or self.env.company).a_default_contract_required,
            }
            
            if farmer.farmer_ref == '/':
                vals['farmer_ref'] = self.env['ir.sequence'].next_by_code('farmer')
            
            farmer.with_context(mail_notrack=True).write(vals)
    
    def action_view_interactions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interactions',
            'res_model': 'farmer.interaction',
            'view_mode': 'list,form',
            'domain': [('farmer_id', '=', self.id)],
            'context': {
                'default_farmer_id':self.id
            }
        }
    
    def action_view_farmer_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offtake Agreements',
            'view_mode': 'list,form',
            'res_model': 'farmer.contract',
            'domain': [('farmer_id', '=', self.id)],
            'context': {
                'default_farmer_id': self.id,
                'default_company_id': self.company_id.id or self.env.company.id,
            },
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    Create the first Offtake Agreement
                </p>
                <p>
                    Odoo helps you easily track all activities related to an offtake agreement contract
                </p>
            """)
        }
    
    def action_view_agrios_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotations & Sales',
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'create': False,
            }
        }
    
    def action_view_agrios_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'RFQs and Purchases',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'create': False,
            }
        }
    
    def action_create_agrios_so(self):
        self.ensure_one()
        
        action = {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Order Inputs'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': {
                'default_partner_id': self.id,
            }
        }
        
        if not self.farmer_requires_contract and self.crop_product_ids:
            allow_operations_out_of_phase = (self.company_id or self.env.company).allow_operations_out_of_phase
            if not (self.open_contract_input_ids or (allow_operations_out_of_phase and self.open_contract_ids)):
                input_products = self.crop_product_ids.mapped('seed_ids') | self.crop_product_ids.mapped('seed_ids.related_inputs_ids') | self.crop_product_ids.mapped('related_inputs_ids')
                
                if input_products:
                    order_line_vals = []
                    
                    for input_prd in input_products:
                        order_line_vals.append((0,0,{
                            'product_id': input_prd.id,
                            'product_uom_qty': (self.total_acreage * input_prd.qty_per_acreage) or 1.0,
                        }))
                    
                    action['context']['default_order_line'] = order_line_vals
        
        return action
    
    def action_create_agrios_po(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name + ' - ' + _('Off-Take'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': {
                'default_partner_id': self.id,
                'default_date_planned': fields.Datetime.now(),
            }
        }
    
    def action_create_farm(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Farm Of %s') % self.display_name,
            'res_model': 'farmer.plot',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_name': _('%s Farm #%d') % (self.display_name, (len(self.plot_ids) + 1)),
                'plot_partner_readonly': True,
            }
        }
        
    def get_offtake_estimate(self, crop_product):
        """Get the total estimate per acre"""
        self.ensure_one()
        estimated_yield = crop_product.estimated_yield
        
        if crop_product.harvest_product_type == 'tree_crop':
            domain = [
                ('plot_id', 'in', self.plot_ids.ids),
                ('product_id', '=', crop_product.id)
            ]
            subplots = self.env['farmer.plot.crop.area'].search(domain)
        
            if subplots:
                total_yield = sum(subplots.mapped('annual_estimated_yield'))
                total_acreage = sum(subplots.mapped('acreage'))
                
                if total_acreage > 0:
                    estimated_yield = total_yield / total_acreage
        
        return estimated_yield
    
    def _get_unreconciled_aml_domain(self):
        super_record = super()
        if hasattr(super_record, '_get_unreconciled_aml_domain'):
            return super_record._get_unreconciled_aml_domain()
        else:
            return [
                ('reconciled', '=', False),
                ('account_id.deprecated', '=', False),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
                ('partner_id', 'in', self.ids),
                ('company_id', 'child_of', self.env.company.id),
            ]
    