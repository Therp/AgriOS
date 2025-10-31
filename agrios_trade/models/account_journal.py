# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    payment_in_kind = fields.Boolean("Payment In Kind Journal", tracking=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if "payment_in_kind_domain" in self._context:
            args = [
                ("payment_in_kind", "=", self._context["payment_in_kind_domain"])
            ] + (args or [])
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
