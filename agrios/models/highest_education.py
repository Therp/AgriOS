from odoo import fields, models


class HighestEducation(models.Model):
    _name = "res.highest.education"
    _description = "Highest Education"

    name = fields.Char(required=True)
