# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class Season(models.Model):
    _name = "season"
    _description = "Planting Season"
    _rec_name = "season"
    _order = "start_date ASC"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    season = fields.Char(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    active = fields.Boolean(default=True, tracking=True)
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Registration Ongoing"),
            ("lock", "Registration Locked"),
            ("closed", "Closed"),
        ],
        default="draft",
        tracking=True,
    )

    expired = fields.Boolean(compute="_compute_expired")

    def unlink(self):
        for season in self:
            if season.status != "draft":
                raise UserError(
                    _(
                        "Only seasons in draft status can be deleted!"
                        " Archive the season instead."
                    )
                )
        return super().unlink()

    def _compute_expired(self):
        for season in self:
            season.expired = (
                season.status in ("open", "lock")
                and season.end_date < fields.Date.today()
            )

    def close_season(self):
        for record in self:
            record.status = "closed"

    def start_registration(self):
        for record in self:
            record.status = "open"

    def lock_registration(self):
        for record in self:
            record.status = "lock"

    def reset_to_draft(self):
        for record in self:
            record.status = "draft"

    _sql_constraints = [
        ("unique_season_name", "UNIQUE(season)", "This Season already exists"),
    ]
