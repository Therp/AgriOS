# -*- coding: utf-8 -*-

from odoo import models, fields, _


class CloudpepperInstanceModuleWizard(models.TransientModel):
    _name = 'cloudpepper.instance.module.wizard'
    _description = 'Add Module to Cloudpepper Instance'
    
    instance_id = fields.Many2one('cloudpepper.instance', required=True, string="Instance")
    repo = fields.Char(required=True, string="Git Repo URL")
    branch = fields.Char(required=True, default="18.0", string="Branch")
    type = fields.Selection([('git', 'Git')], default='git', required=True, string="Type")
    module_name = fields.Char(required=True, help="Optional if the repo has multiple modules")
    
    def action_add_module(self):
        client = self.env['cloudpepper.client'].get_client()
        
        for wizard in self:
            resp = client.add_module(wizard.instance_id.instance_id, wizard.repo, wizard.branch, wizard.type, wizard.module_name)
            wizard.instance_id.message_post(body=_("Started installing module: %s from %s, response %s") % (self.module_name, self.repo, resp))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    