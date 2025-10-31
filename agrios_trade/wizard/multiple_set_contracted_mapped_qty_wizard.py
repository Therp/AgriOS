# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SetMappedQuantitiesWizard(models.TransientModel):
    _name = "multiple.set.contracted.mapped.qty.wizard"
    _description = "Set to Mapped Quantities Multiple Contracts"

    contract_ids = fields.Many2many(
        "farmer.contract",
        string="Draft Contracts To Update",
        domain=[("contract_stage", "=", "draft")],
    )

    @api.model
    def default_get(self, default_fields):
        ret = super().default_get(default_fields)
        if "contract_ids" in default_fields:
            if ret.get("contract_ids"):
                contract_ids = ret["contract_ids"]
            elif self._context.get("active_model") == "farmer.contract":
                contract_ids = self._context.get("active_ids")
            else:
                contract_ids = []
            FarmerContract = self.env["farmer.contract"]
            draft_contracts = (
                self.browse(contract_ids).filtered(lambda r: r.state == "draft")
                if contract_ids
                else FarmerContract  # empty recordset
            )
            if not draft_contracts:
                raise ValidationError(_("No draft contracts selected!"))
            ret["contract_ids"] = [(6, 0, draft_contracts.ids)]
        return ret

    def update_contracts(self):
        self.contract_ids.btn_set_contracted_mapped_qty()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("All %d contracts have been updated.")
                % len(self.contract_ids),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
