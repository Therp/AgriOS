# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_in_kind = fields.Boolean(tracking=True)

    @api.onchange("payment_in_kind", "company_id")
    def _onchange_payment_in_kind(self):
        # TODO RP: Seems very dangerous to blindly set journal_id to False here.
        if self.payment_in_kind:
            if not self.journal_id.payment_in_kind:
                company = self.company_id or self.env.company
                payment_in_kind_journals = self.env["account.journal"].search(
                    [
                        ("payment_in_kind", "=", True),
                        ("type", "=", "sale"),
                        ("company_id", "=", company.id),
                    ]
                )
                if not payment_in_kind_journals:
                    self.payment_in_kind = False
                    warning = {
                        "title": _("Warning!"),
                        "message": _(
                            "No journals defined as a 'payment in kind' journal"
                        ),
                    }
                    return {"warning": warning}
                if len(payment_in_kind_journals) == 1:
                    self.journal_id = payment_in_kind_journals
                else:
                    self.journal_id = False
        else:
            self.journal_id = self._search_default_journal()
