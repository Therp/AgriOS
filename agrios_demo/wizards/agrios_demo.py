# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64

from odoo import models
from odoo.modules.graph import Graph
from odoo.modules.loading import load_data
from odoo.modules.module import get_manifest, get_module_resource

from odoo.addons.base.models.ir_module import assert_log_admin_access


class AgriosDemo(models.TransientModel):
    _name = "agrios.demo"
    _description = "Agrios Demo"

    @assert_log_admin_access
    def action_load_demo_for_agrios(self):
        self.ensure_one()
        env = self.env(su=True)
        currency = env.ref("base.KES")
        currency.write({"active": True})
        env.company.write(
            {
                "name": "AgriGrowth Nairobi",
                "currency_id": currency.id,
                "country_id": env.ref("base.ke").id,
                "logo": self._load_image_base64("demo", "agri-growth-nairobi.png"),
            }
        )

        info = get_manifest("agrios")
        graph = Graph()
        node = graph.add_node("agrios", info)
        graph.update_from_db(env.cr)
        node.demo = True
        load_data(env, {}, "init", kind="demo", package=node)
        env.clear()
        env["res.groups"]._update_user_groups_view()
        env["res.partner"].search([("is_farmer", "=", True)]).verify_farmer()

        # update Department Manager
        env.ref("agrios.department_admin_finance").write(
            {
                "manager_id": env.ref("agrios.employee_1").id,
            }
        )
        env.ref("agrios.department_field_operations").write(
            {
                "manager_id": env.ref("agrios.employee_2").id,
            }
        )
        env.ref("agrios.department_hr_communication").write(
            {
                "manager_id": env.ref("agrios.employee_2").id,
            }
        )
        env.ref("agrios.department_it").write(
            {
                "manager_id": env.ref("agrios.employee_11").id,
            }
        )
        env.ref("agrios.department_monitoring_evaluation").write(
            {
                "manager_id": env.ref("agrios.employee_12").id,
            }
        )
        env.ref("agrios.department_training").write(
            {
                "manager_id": env.ref("agrios.employee_13").id,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/odoo",
        }

    def _load_image_base64(self, *path_parts):
        """Convert an image file into a base64-encoded string."""
        file_path = get_module_resource("agrios_demo", *path_parts)
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data)
