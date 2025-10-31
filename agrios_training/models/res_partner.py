# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_farmer_trainer = fields.Boolean("Farmer Trainer", default=False)
    count_trainings = fields.Integer(compute="_compute_count_trainings")
    certification_ids = fields.One2many("farmer.certification", "farmer_id")
    training_ids = fields.Many2many(
        "farmer.training", domain=[("training_state", "=", "done")]
    )
    count_certifications = fields.Integer(
        "Valid Certifications",
        compute="_compute_certifications",
        help="Number of valid certifications",
    )
    certified = fields.Boolean(
        "Currently Certified",
        compute="_compute_certifications",
        search="_search_certified",
    )

    def _compute_count_trainings(self):
        for rec in self:
            rec.count_trainings = self.env["farmer.contract"].search_count(
                [("farmer_id", "=", rec.id)]
            )

    @api.depends("certification_ids.cert_end_date")
    def _compute_certifications(self):
        today = fields.Date.today()
        for rec in self.sudo():
            rec.count_certifications = self.env["farmer.certification"].search_count(
                [
                    ("farmer_id", "=", rec.id),
                    ("cert_end_date", ">=", today),
                    ("cert_start_date", "<=", today),
                    ("force_expired", "=", False),
                    ("posted", "=", True),
                ]
            )
            if rec.count_certifications:
                rec.certified = True
            else:
                rec.certified = False

    def _search_certified(self, operator, value):
        # TODO RP: operator manipulation has no effect,
        # replace methode without resorting to SQL.
        if (operator == "=" and not value) or (operator == "!=" and value):
            domain_operator = "not in"
        else:
            domain_operator = "in"

        self._cr.execute("""
            SELECT DISTINCT farmer_id
            FROM farmer_certification
            WHERE posted = True
              AND force_expired = FALSE
              AND cert_start_date <= CURRENT_DATE
              AND cert_end_date >= CURRENT_DATE
          """)
        return [("id", domain_operator, [r[0] for r in self._cr.fetchall()])]
