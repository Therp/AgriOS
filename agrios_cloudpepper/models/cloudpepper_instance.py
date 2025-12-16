# -*- coding: utf-8 -*-

import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CloudpepperInstance(models.Model):
    _name = 'cloudpepper.instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cloudpepper Managed Odoo Instance'
    
    name = fields.Char(required=True, tracking=True)
    client_name = fields.Char(required=True, tracking=True)
    instance_url = fields.Char(required=True, tracking=True)
    instance_id = fields.Char(readonly=True, tracking=True)
    default_modules_installed = fields.Boolean(default=False)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('creating', 'Creating'),
        ('started', 'Started'),
        ('error', 'Error')],
        default='draft',
        tracking=True)
    server_id = fields.Many2one(
        'cloudpepper.server', string='Server',
        readonly=True, tracking=True)
    config_data = fields.Text(
        string="Instance Config",
        readonly=True,
        help="Raw JSON of the Odoo config returned by Cloudpepper")

    module_ids = fields.One2many(
        'cloudpepper.instance.module', 'instance_id',
        string='Installed Modules', readonly=True)

    default_repo_url_ids = fields.Many2many('cloudpepper.default.module', 'default_instance_module_rel', 'instance_id', 'module_id',
        string='Default Modules',
        help="Modules to install by default on new instances")

    def action_create_instance(self):
        self.ensure_one()
        
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        self.status = 'creating'
        self.message_post(body="Starting instance creation...")
        try:
            server_id = self.server_id.server_id
            data = client.create_instance(server_id, self.name, self.instance_url)
            self.instance_id = data.get('id')
            self.status = 'running'
            self.message_post(body=f"Instance created successfully: **{self.instance_id}**")
        
        except UserError as e:
            self._cr.rollback()
            self.status = 'error'
            self.message_post(body=f"Error creating instance:\n{e}")
            self._cr.commit()
            raise
    
    def action_deploy_modules(self):
        self.ensure_one()
        
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        if not self.instance_id:
            raise UserError(_("Instance must be created before deploying modules."))

        try:
            for mod in self.default_repo_url_ids:
                resp = client.add_module(self.instance_id, mod.repo, mod.branch, mod.type, mod.module_name)
            self.default_modules_installed = True
            self.message_post(body="Modules deployed successfully.")
        
        except UserError as e:
            self._cr.rollback()
            self.status = 'error'
            self.message_post(body=f"Error deploying modules:\n{e}")
            self._cr.commit()
            raise
    
    @api.model
    def action_fetch_instances(self):
        """Sync all instances from the API into local records."""
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        data = client.list_instances()
        for inst in data:
            vals = {
                'client_name': inst.get('name'),
                'name': inst.get('name'),
                'instance_url': inst.get('domain'),
                'instance_id': inst.get('id'),
                'status': inst.get('status'),
            }
            server_ref = inst.get('serverId')
            if server_ref:
                srv = self.env['cloudpepper.server'].search(
                    [('server_id', '=', server_ref)], limit=1)
                if srv:
                    vals['server_id'] = srv.id
            rec = self.search([('instance_id', '=', inst.get('id'))], limit=1)
            if rec:
                rec.write(vals)
            else:
                self.create(vals)
    
    def action_fetch_config(self):
        """Fetch /instances/{id}/config and store it in config_data."""
        self.ensure_one()
        
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        if not self.instance_id:
            raise UserError(_("Instance must be created first."))
        
        try:
            data = client.get_instance_config(self.instance_id)
            pretty = json.dumps(data, indent=2)
            self.config_data = pretty
            self.message_post(body="Instance config fetched and stored.")
        
        except UserError as e:
            self._cr.rollback()
            self.message_post(body=f"Error fetching config:\n{e}")
            self._cr.commit()
            raise
    
    def action_fetch_installed_modules(self):
        """Fetch /instances/{id}/installed-modules and persist per‐module records."""
        self.ensure_one()
        
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        if not self.instance_id:
            raise UserError(_("Instance must be created first."))
        
        raw = client.list_installed_modules(self.instance_id)
        # raw is a dict: { module_name: { 'latest_version': '18.0.x.x' }, ... }
        
        to_keep = []
        for module_name, info in raw.items():
            version = info.get('latest_version') or ''
            rec = self.env['cloudpepper.instance.module'].search([
                ('instance_id', '=', self.id),
                ('name', '=', module_name),
            ], limit=1)
            vals = {'latest_version': version}
            
            if rec:
                rec.write(vals)
            else:
                rec = self.env['cloudpepper.instance.module'].create({
                    'instance_id': self.id,
                    'name': module_name,
                    **vals
                })
            
            to_keep.append(rec.id)
        
        # Optionally remove modules no longer reported
        self.env['cloudpepper.instance.module'].search([
            ('instance_id', '=', self.id),
            ('id', 'not in', to_keep)
        ]).unlink()
        
        self.message_post(body="Installed-modules list synchronized.")
    
    def _fetch_instance_users(self):
        self.ensure_one()
        
        client = self.env['cloudpepper.client'].get_client()
        if not client:
            raise UserError(_('Cloudpepper configurations not set!'))
        
        if not self.instance_id:
            raise UserError(_("Instance must be created first."))
        
        raw = client.list_users(self.instance_id)
    
    def open_add_module_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cloudpepper.instance.module.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_instance_id': self.id,
            },
        }
    