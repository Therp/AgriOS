# -*- coding: utf-8 -*-

from odoo import models, fields


class IdType(models.Model):
    _name = 'res.id.type'
    _description = 'ID Type'

    name = fields.Char(string='Name', required=True)
