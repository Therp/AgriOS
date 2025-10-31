# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CorrectiveAction(models.Model):
    _name = "corrective.action"
    _description = "Corrective Action"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Corrective action code needs to be unique!"),
    ]
