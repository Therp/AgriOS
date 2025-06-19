# -*- coding: utf-8 -*-

from odoo import models, fields

class HighestEducation(models.Model):
    _name = 'res.highest.education'
    _description = 'Highest Education'

    name = fields.Char(string='Name', required=True)
