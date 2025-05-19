# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from collections import defaultdict


class Farmer(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'phone', 'outgrower_ref']
    
    @api.model
    def _get_farm_uom_domain(self):
        return [('category_id.id', '=', self.env.ref('uom.uom_categ_surface').id), ('uom_type','=','bigger')]
    
    @api.model
    def _default_farm_uom(self):
        farm_uom = int(self.env['ir.config_parameter'].sudo().get_param('outgrower_management.farm_uom') or 0)
        if not farm_uom:
            farm_uom = self.env.ref('agrios.area_1', raise_if_not_found=False)
        return farm_uom
    
    is_outgrower = fields.Boolean('Outgrower', default=False)
    is_farmer_trainer = fields.Boolean('Farmer Trainer', default=False)
    outgrower_requires_contract = fields.Boolean('Requires Contract', tracking=True, default=False, help="If selected, this outgrower will require a valid offtake agreement contract to sell inputs or to buy off-takes. If unselected, no valid contract is needed for sales or purchases.")
    
    outgrower_ref = fields.Char('Outgrower Reference', default='/', readonly=True, copy=False)
    
    farmer_group_id = fields.Many2one('farmer.group', 'Farmers Group', domain="[('coop_id', '=?', coop_id)]", tracking=True)
    coop_id = fields.Many2one('cooperative', 'Location Area 1', ondelete='restrict', tracking=True)
    district_id = fields.Many2one('district', 'Location Area 2', ondelete='restrict', tracking=True)
    region_id = fields.Many2one('region', 'Location Area 3', ondelete='restrict', tracking=True)
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
    
    community_facilitator_id = fields.Many2one(related='coop_id.community_facilitator_id')
    
    # Basic outgrower details
    gender = fields.Selection([('female', 'Female'), ('male', 'Male')], string='Gender')
    outgrower_identification = fields.Char(string='National ID', tracking=True)
    society_id = fields.Char(string='Society ID', tracking=True)
    birthday = fields.Date(string='Date of Birth')
    age = fields.Integer(compute='_compute_age')
    outgrower_stage = fields.Selection([('draft', 'Draft'),('verified', 'Verified')], 'Outgrower Stage', default='draft', copy=False)
    
    # farm details
    farm_acreage = fields.Float('Own Farm', compute='_compute_land_acreage', inverse='_inverse_farm_acreage', store=True, tracking=True)
    leased_acreage = fields.Float('Leased Farm', compute='_compute_land_acreage', inverse='_inverse_leased_acreage', store=True, tracking=True)
    total_land_size = fields.Float('Total Farm', compute='_compute_total_land_size', store=True)
    utilized_acreage = fields.Float('Utilized Farm', compute='_compute_utilized_acreage')
    unutilized_acreage = fields.Float('Unutilized Farm', compute='_compute_unutilized_acreage')
    
    plot_ids = fields.One2many('res.partner.area', 'partner_id', 'Responsible Area', copy=False)
    
    # Linked Offtake Agreements
    count_offtake_agreements = fields.Integer(compute='_compute_count_offtake_agreements')
    offtake_agreement_ids = fields.One2many('offtake.agreement', 'outgrower_id', 'Contracts')
    
    open_contract_ids = fields.One2many('offtake.agreement', string='Open Contracts', compute='_compute_open_contracts')
    open_contract_input_ids = fields.One2many('offtake.agreement', string='Open Contracts [Input State]', compute='_compute_open_contracts')
    open_contract_harvest_ids = fields.One2many('offtake.agreement', string='Open Contracts [Harvest State]', compute='_compute_open_contracts')
    
    count_input_sales = fields.Integer(compute='_compute_count_input_sales')
    count_harvest_offtakes = fields.Integer(compute='_compute_count_harvest_offtakes')
    count_trainings = fields.Integer(compute='_compute_count_trainings')
    
    certification_ids = fields.One2many('farmer.certification', 'outgrower_id')
    
    training_ids = fields.Many2many('farmer.training', domain=[('training_state', '=', 'done')])
    
    harvest_crop_ids = fields.Many2many('product.product', 'res_partner_product_harvest_crops_rel', 'partner_id', 'product_id', 'Harvest Crops', domain=[('harvest_product','=',True)])
    
    farm_uom = fields.Many2one('uom.uom', 'Unit of Measure', domain=lambda self: self._get_farm_uom_domain(), default=lambda self: self._default_farm_uom(), tracking=True)
    
    # extra farmer info
    family_size = fields.Integer()
    coop_shares = fields.Integer()
    next_of_kin = fields.Char()
    nok_id = fields.Char(string='NOK ID')
    nok_phone = fields.Char(string='NOK Phone')
    
    count_certifications = fields.Integer('Valid Certifications', compute='_compute_certifications', help="Number of valid certifications")
    certified = fields.Boolean('Currently Certified', compute='_compute_certifications', search='_search_certified')
    
    has_expired_contract = fields.Boolean(compute='_compute_has_expired_contract')
    
    can_order_inputs = fields.Boolean('Can Order Inputs [Without Confirmation]', compute='_compute_can_order_inputs')
    can_order_inputs_confirm = fields.Boolean('Can Order Inputs [With Confirmation]', compute='_compute_can_order_inputs')
    
    can_regist_offtakes = fields.Boolean('Can Register Off-Takes [Without Confirmation]', compute='_compute_can_regist_offtakes')
    can_regist_offtakes_confirm = fields.Boolean('Can Register Off-Takes [With Confirmation]', compute='_compute_can_regist_offtakes')
    
    country_id = fields.Many2one(required=True, default=lambda self: self.env.company.country_id)
    interactions_count = fields.Integer(compute='_compute_interactions_count', string='Interactions')
    
    agrios_unreconciled_aml_ids = fields.One2many('account.move.line', compute='_compute_agrios_unreconciled_aml_ids', readonly=False) # copy of enterprise unreconciled_aml_ids
    
    @api.depends('invoice_ids')
    @api.depends_context('company', 'allowed_company_ids')
    def _compute_agrios_unreconciled_aml_ids(self):
        if not self: return
        
        if hasattr(self[0], 'unreconciled_aml_ids'):
            for ptn in self:
                ptn.agrios_unreconciled_aml_ids = ptn.unreconciled_aml_ids
        
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
                partner.agrios_unreconciled_aml_ids = self.env['account.move.line'].browse(unreconciled_aml_ids.get(partner, []))
    
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
    
    @api.depends('plot_ids', 'plot_ids.farm_size')
    def _compute_land_acreage(self):
        for outgrower in self:
            if outgrower.plot_ids:
                outgrower.farm_acreage = sum(outgrower.plot_ids.filtered(lambda plot: plot.is_owner).mapped('farm_size'))
                outgrower.leased_acreage = sum(outgrower.plot_ids.filtered(lambda plot: not plot.is_owner).mapped('farm_size'))
            else:
                outgrower.farm_acreage = outgrower.leased_acreage = 0.0
    
    def _inverse_farm_acreage(self):
        """Allows manual updates to farm_acreage via import"""
        for record in self:
            record.farm_acreage = record.farm_acreage
    
    def _inverse_leased_acreage(self):
        """Allows manual updates to leased_acreage via import"""
        for record in self:
            record.leased_acreage = record.leased_acreage

    @api.depends('farm_acreage', 'leased_acreage')
    def _compute_total_land_size(self):
        for rec in self:
            rec.total_land_size = rec.farm_acreage + rec.leased_acreage
    
    @api.depends('outgrower_stage', 'outgrower_requires_contract', 'company_id')
    def _compute_can_order_inputs(self):
        for farmer in self:
            if farmer.outgrower_stage == 'verified':
                if farmer.open_contract_input_ids:
                    farmer.can_order_inputs = True
                    farmer.can_order_inputs_confirm = False
                elif farmer.open_contract_harvest_ids:
                    farmer.can_order_inputs_confirm = (farmer.company_id or self.env.company).agrios_allow_operations_out_of_phase
                    farmer.can_order_inputs = not farmer.can_order_inputs_confirm and not farmer.outgrower_requires_contract
                else:
                    farmer.can_order_inputs = not farmer.outgrower_requires_contract
                    farmer.can_order_inputs_confirm = False
            else:
                farmer.can_order_inputs = farmer.can_order_inputs_confirm = False
    
    @api.depends('outgrower_stage', 'outgrower_requires_contract', 'company_id')
    def _compute_can_regist_offtakes(self):
        for farmer in self:
            if farmer.outgrower_stage == 'verified':
                if farmer.open_contract_harvest_ids:
                    farmer.can_regist_offtakes = True
                    farmer.can_regist_offtakes_confirm = False
                elif farmer.open_contract_input_ids:
                    farmer.can_regist_offtakes_confirm = (farmer.company_id or self.env.company).agrios_allow_operations_out_of_phase
                    farmer.can_regist_offtakes = not farmer.can_regist_offtakes_confirm and not farmer.outgrower_requires_contract
                else:
                    farmer.can_regist_offtakes = not farmer.outgrower_requires_contract
                    farmer.can_regist_offtakes_confirm = False
            else:
                farmer.can_regist_offtakes = farmer.can_regist_offtakes_confirm = False
    
    def _compute_has_expired_contract(self):
        for farmer in self:
            farmer.has_expired_contract = any(farmer.offtake_agreement_ids.mapped('expired_contract'))
    
    def _compute_open_contracts(self):
        for farmer in self:
            farmer.open_contract_ids = farmer.offtake_agreement_ids.filtered(lambda cont: cont.contract_stage == 'open')
            farmer.open_contract_input_ids = farmer.open_contract_ids.filtered(lambda cont: not cont.ready_for_harvest)
            farmer.open_contract_harvest_ids = farmer.open_contract_ids.filtered(lambda cont: cont.ready_for_harvest)
    
    def _compute_count_offtake_agreements(self):
        for rec in self:
            rec.count_offtake_agreements = self.env['offtake.agreement'].search_count([('outgrower_id', '=', rec.id)])
    
    def _compute_count_input_sales(self):
        for rec in self:
            rec.count_input_sales = self.env['sale.order'].search_count([('partner_id', '=', rec.id)])
    
    def _compute_count_harvest_offtakes(self):
        for rec in self:
            rec.count_harvest_offtakes = self.env['purchase.order'].search_count([('partner_id', '=', rec.id)])
    
    def _compute_count_trainings(self):
        for rec in self:
            rec.count_trainings = self.env['offtake.agreement'].search_count([('outgrower_id', '=', rec.id)])
    
    @api.depends('certification_ids.cert_end_date')
    def _compute_certifications(self):
        today = fields.Date.today()
        
        for rec in self.sudo():
            rec.count_certifications = self.env['farmer.certification'].search_count([
                ('outgrower_id','=',rec.id), ('cert_end_date','>=',today),
                ('cert_start_date','<=',today), ('force_expired','=',False),
                ('posted','=',True),
            ])
            if rec.count_certifications:
                rec.certified = True
            else:
                rec.certified = False
    
    def _compute_utilized_acreage(self):
        for partner in self:
            partner.utilized_acreage = sum(partner.offtake_agreement_ids.filtered(lambda contract: contract.contract_stage == 'open').mapped('contracted_farm_acreage'))
    
    def _compute_unutilized_acreage(self):
        for rec in self:
            rec.unutilized_acreage = rec.total_land_size - rec.utilized_acreage
    
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
        
    @api.depends('outgrower_ref')
    def _compute_display_name(self):
        ret = super()._compute_display_name()
        
        for partner in self:
            if partner.outgrower_ref and partner.outgrower_ref != '/':
                partner.display_name = f"[{partner.outgrower_ref}] {partner.display_name or ''}"
        
        return ret
        
    def _compute_interactions_count(self):
        for partner in self:
            partner.interactions_count = self.env['farmer.interaction'].search_count([('outgrower_id', '=', partner.id)])
    
    def _search_certified(self, operator, value):
        if (operator == '=' and not value) or (operator == '!=' and value):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        
        self._cr.execute("""
            SELECT DISTINCT outgrower_id
            FROM farmer_certification
            WHERE posted = True
              AND force_expired = FALSE
              AND cert_start_date <= CURRENT_DATE
              AND cert_end_date >= CURRENT_DATE
          """)
        return [('id', domain_operator, [r[0] for r in self._cr.fetchall()])]
    
    @api.onchange('farmer_group_id')
    def _onchange_farmer_group(self):
        if self.farmer_group_id.coop_id:
            self.coop_id = self.farmer_group_id.coop_id
    
    @api.onchange('coop_id')
    def _onchange_coop_id(self):
        if self.coop_id:
            self.district_id = self.coop_id.district_id
            
            if self.farmer_group_id and self.coop_id != self.farmer_group_id.coop_id:
                self.farmer_group_id = False
    
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
                self.region_id = False
                self.district_id = False
                self.coop_id = False
    
    @api.onchange('loc_area_6_id')
    def _onchange_loc_area_6_id(self):
        if self.loc_area_6_id:
            if self.loc_area_5_id and self.loc_area_5_id.parent_id != self.loc_area_6_id:
                self.loc_area_5_id = False
                self.loc_area_4_id = False
                self.region_id = False
                self.district_id = False
                self.coop_id = False
    
    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if self._context.get('filter_duplicate_identification'):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id AND ptn1.outgrower_identification = ptn2.outgrower_identification
                WHERE ptn1.outgrower_identification IS NOT NULL
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
        
        if view_type == 'search' and view == self.env.ref('agrios.view_outgrower_search_filter', raise_if_not_found=False):
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
            
            lev3 = arch.xpath("//filter[@name='groupby_region_id']")[0]
            if max_level >= 3:
                lev3.set('string', loc_details[3])
            else:
                lev3.getparent().remove(lev3)
            
            lev2 = arch.xpath("//filter[@name='groupby_district_id']")[0]
            if max_level >= 2:
                lev2.set('string', loc_details[2])
            else:
                lev2.getparent().remove(lev2)
            
            lev1 = arch.xpath("//filter[@name='groupby_coop_id']")[0].set('string', loc_details[1])
        
        elif view_type == 'list' and view == self.env.ref('agrios.view_outgrower_tree', raise_if_not_found=False):
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
    
    def verify_outgrower(self):
        for outgrower in self:
            vals = {
                'outgrower_stage': 'verified',
                'outgrower_requires_contract': (outgrower.company_id or self.env.company).agrios_default_contract_needed,
            }
            
            if outgrower.outgrower_ref == '/':
                vals['outgrower_ref'] = self.env['ir.sequence'].next_by_code('outgrower.farmer')
            
            outgrower.with_context(mail_notrack=True).write(vals)
    
    def action_view_interactions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interactions',
            'res_model': 'farmer.interaction',
            'view_mode': 'list,form',
            'domain': [('outgrower_id', '=', self.id)],
            'context': {
                'default_outgrower_id':self.id
            }
        }
    
    def action_view_offtake_agreements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offtake Agreements',
            'view_mode': 'list,form',
            'res_model': 'offtake.agreement',
            'domain': [('outgrower_id', '=', self.id)],
            'context': {
                'default_outgrower_id': self.id,
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
        
        if not self.outgrower_requires_contract and self.harvest_crop_ids:
            agrios_allow_operations_out_of_phase = (self.company_id or self.env.company).agrios_allow_operations_out_of_phase
            if not (self.open_contract_input_ids or (agrios_allow_operations_out_of_phase and self.open_contract_ids)):
                input_products = self.harvest_crop_ids.mapped('seed_ids') | self.harvest_crop_ids.mapped('seed_ids.related_inputs_ids') | self.harvest_crop_ids.mapped('related_inputs_ids')
                
                if input_products:
                    order_line_vals = []
                    
                    for input_prd in input_products:
                        order_line_vals.append((0,0,{
                            'product_id': input_prd.id,
                            'product_uom_qty': (self.total_land_size * input_prd.qty_per_acreage) or 1.0,
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
            'res_model': 'res.partner.area',
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
        estimated_yield = crop_product.est_yield
        
        if crop_product.harvest_product_type == 'tree_crop':
            domain = [
                ('plot_id', 'in', self.plot_ids.ids),
                ('product_id', '=', crop_product.id)
            ]
            subplots = self.env['res.partner.subplot'].search(domain)
        
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
    