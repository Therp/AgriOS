# -*- coding: utf-8 -*-

from odoo import models, fields


class CloudpepperInstanceUser(models.Model):
    _name = 'cloudpepper.instance.user'
    _description = 'Users on Cloudpepper Instance'
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