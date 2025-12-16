# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SetupInstanceWizard(models.TransientModel):
    _name = 'cloudpepper.setup.wizard'
    _description = 'Wizard: Create & Deploy Cloudpepper Instance'

    server_id = fields.Many2one('cloudpepper.server', string='Server', required=True)
    client_name = fields.Char(required=True)
    instance_name = fields.Char(required=True)
    instance_url = fields.Char(required=True, compute='_compute_instance_url', store=True,
       readonly=False, help="URL to access the instance")
    repo_url_ids = fields.Many2many('cloudpepper.default.module', 'default_module_rel', 'setup_id', 'module_id',
        string='Default Modules',
        compute='_compute_repo_url_ids',
        store=True,
        readonly=False,
        help="Modules to install by default on new instances")
    
    @api.depends('server_id')
    def _compute_instance_url(self):
        for wizard in self:
            sudomain = self.env['ir.sequence'].next_by_code('cloudpepper.subdomain')
            wizard.instance_url = f"{sudomain}.cloudpepper.site"
    
    @api.depends('server_id')
    def _compute_repo_url_ids(self):
        modules = self.env['cloudpepper.default.module'].search([])
        for wizard in self:
            wizard.repo_url_ids = [(6, 0, modules.ids)]
    
    def action_run(self):
        self.ensure_one()
        
        inst = self.env['cloudpepper.instance'].create({
            'server_id': self.server_id.id,
            'client_name': self.client_name,
            'name': self.instance_name,
            'instance_url': self.instance_url,
            'default_repo_url_ids': self.repo_url_ids,
        })
        
        return {
            'name': _('Cloudpepper Instance'),
            'view_mode': 'form',
            'res_model': 'cloudpepper.instance',
            'res_id': inst.id,
            'type': 'ir.actions.act_window',
        }
    