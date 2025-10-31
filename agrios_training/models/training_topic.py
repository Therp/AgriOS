# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TrainingTopic(models.Model):
    _name = "training.topic"
    _description = "Training Topic"
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "Training Topic already Exists"),
    ]
