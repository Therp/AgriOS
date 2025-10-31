# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class FarmerTraining(models.Model):
    _name = "farmer.training"
    _description = "Farmer Training"
    _inherit = ["mail.thread", "mail.activity.mixin", "agrios.area.mixin"]
    _order = "training_date desc"

    name = fields.Char("Training No.", compute="_compute_name")
    active = fields.Boolean(default=True, tracking=True)
    training_ids = fields.Many2many("training.topic", tracking=True, required=True)
    trainer_id = fields.Many2one(
        "res.partner",
        required=True,
        tracking=True,
        domain=[("is_farmer_trainer", "=", True)],
    )
    training_state = fields.Selection(
        [
            ("planned", "Planned"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="planned",
        tracking=True,
        string="Status",
    )
    training_date = fields.Date(required=True)
    training_start_time = fields.Float()
    training_duration = fields.Float(default=1.0)
    training_location = fields.Char("Location/Venue", required=True, tracking=True)
    training_type = fields.Selection(
        [("internal", "Internal"), ("external", "External")],
        default="internal",
        tracking=True,
    )
    training_content = fields.Text("Summary")
    count_training_participants = fields.Integer(
        "#Participants", compute="_compute_count_training_participants"
    )
    training_participants_ids = fields.Many2many(
        "res.partner",
        domain=[("is_farmer", "=", True), ("farmer_stage", "=", "verified")],
    )
    farmer_group_ids = fields.Many2many(
        "farmer.group",
        string="Farmer Groups",
        tracking=True,
    )
    country_id = fields.Many2one(
        "res.country",
        "Country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )

    def _compute_name(self):
        for rec in self:
            rec.name = _("Training") + f" - {rec.id}"

    @api.depends("training_participants_ids")
    def _compute_count_training_participants(self):
        for rec in self:
            rec.count_training_participants = len(rec.training_participants_ids)

    def action_done(self):
        self.write({"training_state": "done"})

    def action_cancel(self):
        self.write({"training_state": "cancelled"})

    def action_planned(self):
        self.write({"training_state": "planned"})
