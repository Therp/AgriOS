# -*- coding: utf-8 -*-

from odoo import models, fields


class CloudpepperInstanceModule(models.Model):
    _name = 'cloudpepper.instance.module'
    _description = 'Installed Module on Cloudpepper Instance'
    _order = 'name'

    instance_id = fields.Many2one(
        'cloudpepper.instance',
        string='Instance',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Module Name',
        required=True,
        index=True,
    )
    latest_version = fields.Char(
        string='Latest Version',
        required=True,
    )
    