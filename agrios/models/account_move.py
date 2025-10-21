from odoo import _, api, fields, models
from odoo.tools import SQL, Query


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_in_kind = fields.Boolean(tracking=True)

    @api.onchange("payment_in_kind", "company_id")
    def _onchange_payment_in_kind(self):
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


class AccountMoveLine(models.Model):  # from ac_followup
    _inherit = "account.move.line"

    def _read_group_groupby(self, groupby_spec: str, query: Query) -> SQL:
        if groupby_spec != "followup_overdue":
            return super()._read_group_groupby(groupby_spec, query)
        return SQL(
            """COALESCE(%s, %s) < %s""",
            self._field_to_sql(self._table, "date_maturity", query),
            self._field_to_sql(self._table, "date", query),
            fields.Date.context_today(self),
        )

    def _read_group_empty_value(self, spec):
        if spec != "followup_overdue":
            return super()._read_group_empty_value(spec)
        return False

    def _read_group_postprocess_groupby(self, groupby_spec, raw_values):
        if groupby_spec != "followup_overdue":
            return super()._read_group_postprocess_groupby(groupby_spec, raw_values)
        return ((value or False) for value in raw_values)
