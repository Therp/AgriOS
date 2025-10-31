# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools import SQL, Query


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # TODO RP: Find out what the purpose of these functions are...

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
