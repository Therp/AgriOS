# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class PartnerEducation(models.Model):
    _name = "partner.education"
    _description = "Partner Education"

    name = fields.Char(required=True)
