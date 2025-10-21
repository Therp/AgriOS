from odoo import fields, models


class IdType(models.Model):
    _name = "res.id.type"
    _description = "ID Type"

    name = fields.Char(required=True)
