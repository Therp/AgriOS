# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cloudpepper_api_url = fields.Char(
        string="Cloudpepper API URL",
        config_parameter='cloudpepper.api_url',
    )
    cloudpepper_api_key = fields.Char(
        string="Cloudpepper API Key",
        config_parameter='cloudpepper.api_key',
    )