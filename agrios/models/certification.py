# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import index_exists
from markupsafe import Markup
from dateutil.relativedelta import relativedelta


class CertificationType(models.Model):
    _name = 'certification.type'
    _description = 'Certification Type'
    _order = 'name'
    
    name = fields.Char('Certification Type', required=True)
    certifying_organisation_id = fields.Many2one('res.partner', 'Certifying Organization', ondelete='restrict')
    validity_period = fields.Integer('Validity (Months)', default=12, required=True)
    style = fields.Selection([('info','Blue'),('muted','Grey'),('success','Green'),('warning','Orange'),('danger','Red')], 'Color Style')
    active = fields.Boolean(default=True)
    certification_ids = fields.One2many('farmer.certification', 'certification_type_id')
    farmer_count = fields.Integer('Certified Farmers', compute='_compute_farmer_count')
    
    _sql_constraints = [
        ('_check_validity', 'CHECK(validity_period > 0)', "Validity Period MUST be greater than zero"),
    ]
    
    def _compute_farmer_count(self):
        for rec in self:
            rec.farmer_count = len(rec.certification_ids.mapped('farmer_id'))
    

class CorrectiveAction(models.Model):
    _name = 'corrective.action'
    _description = 'Corrective Action'
    _order = 'name'
    
    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Corrective action code needs to be unique!'),
    ]
    

class FarmerCertification(models.Model):
    _name = 'farmer.certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Farmer Certification'
    _order = 'cert_end_date DESC'
    
    farmer_id = fields.Many2one('res.partner', required=True, tracking=True, index=True, domain=[('is_farmer','=',True),('farmer_stage','=','verified')])
    certification_type_id = fields.Many2one('certification.type', required=True, tracking=True)
    cert_serial_num = fields.Char('Serial No.', tracking=True, readonly=True)
    cert_start_date = fields.Date('Start Date', required=True, tracking=True, readonly=True)
    cert_end_date = fields.Date('End Date', compute='_compute_cert_end_date', store=True)
    active = fields.Boolean(default=True, tracking=True)
    state = fields.Selection([('draft','Draft'),('valid','Valid'),('expired','Expired'),('force_expired','Force Expired')], compute='_compute_state')
    origin = fields.Selection([('manual', 'Manual')], default='manual', required=True, readonly=True, copy=False)
    final_score = fields.Integer('Final Score', help='Final certification score between 0 and 100. [0, 100]', tracking=True, readonly=True)
    corrective_action_ids = fields.Many2many('corrective.action', 'certified_farmer_corrective_actions_rel', 'certification_id', 'corrective_action_id', 'Corrective Actions', readonly=True)
    posted = fields.Boolean('Certification Validated', readonly=True, copy=False)
    force_expired = fields.Boolean('Force Expired', readonly=True, copy=False)
    
    style = fields.Selection(related='certification_type_id.style', readonly=True)
    
    valid_farmer_certification_ids = fields.Many2many('farmer.certification', compute='_compute_valid_farmer_certification', string="Valid Farmer Certifications")
    valid_farmer_certification_count = fields.Integer(compute='_compute_valid_farmer_certification')
    display_name = fields.Char(compute='_compute_display_name', store=True, compute_sudo=True)
    
    @api.depends('farmer_id', 'state')
    def _compute_valid_farmer_certification(self):
        for certification in self:
            certification.valid_farmer_certification_ids = certification.farmer_id.certification_ids.filtered(lambda cert: cert != certification and cert.state == 'valid')
            certification.valid_farmer_certification_count = len(certification.valid_farmer_certification_ids)
    
    @api.depends('certification_type_id', 'cert_start_date')
    def _compute_cert_end_date(self):
        for certification in self:
            if certification.cert_start_date and certification.certification_type_id:
                certification.cert_end_date = (certification.cert_start_date + relativedelta(months=certification.certification_type_id.validity_period) - relativedelta(days=1))
            else:
                certification.cert_end_date = False
    
    @api.depends('posted', 'force_expired', 'cert_end_date')
    def _compute_state(self):
        today = fields.Date.today()
        
        for certification in self:
            if not certification.posted:
                certification.state = 'draft'
            elif certification.force_expired:
                certification.state = 'force_expired'
            elif not certification.cert_end_date or today <= certification.cert_end_date:
                certification.state = 'valid'
            else:
                certification.state = 'expired'
    
    @api.depends('farmer_id.name', 'certification_type_id.name', 'cert_start_date')
    def _compute_display_name(self):
        for certification in self:
            if certification.farmer_id and certification.certification_type_id and certification.cert_start_date:
                certification.display_name = f"{self.farmer_id.name} - {self.certification_type_id.name} - {self.cert_start_date.year}"
            else:
                certification.display_name = _('Draft Certification')
    
    @api.constrains('final_score')
    def _check_final_score(self):
        for certification in self:
            if certification.final_score > 100 or certification.final_score < 0:
                raise ValidationError(_('The final score needs to be between 0 and 100. [0, 100]'))
    
    def _auto_init(self):
        super()._auto_init()
        if not index_exists(self.env.cr, 'farmer_certification_certified_idx'):
            self.env.cr.execute("CREATE INDEX farmer_certification_certified_idx ON farmer_certification(posted, force_expired, cert_start_date, cert_end_date)")
    
    def btn_validate(self):
        self.action_validate()
        
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Certification validated!"),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
    
    def btn_set_draft(self):
        self.action_set_draft()
        
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Certification set to draft!"),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
    
    def action_validate(self):
        for certification in self:
            if not certification.posted:
                certification.posted = True
                certification.message_post(body=_('Certification validated'))
                
                for valid_farmer_certification in certification.valid_farmer_certification_ids.sudo():
                    valid_farmer_certification.force_expired = True
                    valid_farmer_certification.message_post(body=Markup(_('This Certification record was set as expired due to a new one being added: %s') % certification._get_html_link()))
    
    def action_set_draft(self):
        for certification in self:
            if certification.posted:
                certification.posted = False
                certification.force_expired = False
                certification.message_post(body=_('Certification set to draft'))
    