# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TrainingTopic(models.Model):
    _name = 'training.topic'
    _description = 'Training Topic'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Training Topic already Exists'),
    ]


class FarmerTraining(models.Model):
    _name = 'farmer.training'
    _description = 'Farmer Training'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'training_date desc'
    
    name = fields.Char("Training No.", compute='_compute_name')
    active = fields.Boolean(default=True, tracking=True)
    training_ids = fields.Many2many('training.topic', tracking=True, required=True)
    trainer_id = fields.Many2one('res.partner', required=True, tracking=True, domain=[('is_farmer_trainer','=',True)])
    training_state = fields.Selection([
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ], default='planned', tracking=True, string='Status')
    training_date = fields.Date(required=True)
    training_start_time = fields.Float()
    training_duration = fields.Float(default=1.0)
    training_location = fields.Char('Location/Venue', required=True, tracking=True)
    training_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default='internal', tracking=True)
    training_content = fields.Text('Summary')
    count_training_participants = fields.Integer('#Participants', compute='_compute_count_training_participants')
    training_participants_ids = fields.Many2many('res.partner', domain=[('is_outgrower','=',True),('outgrower_stage','=','verified')])
    farmer_group_ids = fields.Many2many('farmer.group', string='Groups', domain="[('loc_area_1_id', '=?', loc_area_1_id)]", tracking=True)
    
    loc_area_1_id = fields.Many2one('area.level.1', string='Location Area 1', ondelete='restrict', required=True, tracking=True)
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
    
    def init(self):
        super().init()
        self._cr.execute("""
            UPDATE farmer_training
            SET loc_area_2_id = ll1.parent_id
            FROM area_level_1 ll1
            WHERE farmer_training.loc_area_1_id = ll1.id
            AND farmer_training.loc_area_2_id IS NULL;
            
            UPDATE farmer_training
            SET loc_area_3_id = ll2.parent_id
            FROM area_level_2 ll2
            WHERE farmer_training.loc_area_2_id = ll2.id
            AND farmer_training.loc_area_3_id IS NULL;
        """)
    
    def _compute_name(self):
        for rec in self:
            rec.name = _('Training') + f" - {rec.id}"
    
    @api.depends('training_participants_ids')
    def _compute_count_training_participants(self):
        for rec in self:
            rec.count_training_participants = len(rec.training_participants_ids)
    
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
    
    @api.onchange('loc_area_1_id')
    def _onchange_loc_area_1_id(self):
        if self.loc_area_1_id:
            self.loc_area_2_id = self.loc_area_1_id.parent_id
            
        if self.loc_area_1_id and self.farmer_group_ids and self.loc_area_1_id != self.farmer_group_ids[0].loc_area_1_id:
            self.farmer_group_ids = False
    
    @api.onchange('loc_area_2_id')
    def _onchange_loc_area_2_id(self):
        if self.loc_area_2_id:
            self.loc_area_3_id = self.loc_area_2_id.parent_id
            
            if self.loc_area_1_id and self.loc_area_1_id.parent_id != self.loc_area_2_id:
                self.loc_area_1_id = False
    
    @api.onchange('loc_area_3_id')
    def _onchange_loc_area_3_id(self):
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
    
    @api.onchange('farmer_group_ids')
    def _onchange_farmer_group(self):
        for rec in self:
            if rec.farmer_group_ids.loc_area_1_id:
                rec.loc_area_1_id = rec.farmer_group_ids.loc_area_1_id[0]
            else:
                rec.loc_area_1_id = False
            rec.training_participants_ids = self.env['res.partner'].search([('is_outgrower','=',True),('outgrower_stage','=','verified'),('farmer_group_id','in',rec.farmer_group_ids.ids)])
    
    def action_done(self):
        self.write({'training_state': 'done'})
    
    def action_cancel(self):
        self.write({'training_state': 'cancelled'})
    
    def action_planned(self):
        self.write({'training_state': 'planned'})
    