# -*- coding: utf-8 -*-
from odoo import models, fields


class CloudpepperDefaultModule(models.Model):
    _name = 'cloudpepper.default.module'
    _description = 'Default Modules for Initial Setup'

    repo = fields.Char(required=True, string="Git Repo URL")
    branch = fields.Char(required=True, default="18.0", string="Branch")
    type = fields.Selection([('git', 'Git')], default='git', required=True, string="Type")
    module_name = fields.Char(help="Optional if the repo has multiple modules")
    active = fields.Boolean(default=True, readonly=True)