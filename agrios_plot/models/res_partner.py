# Copyright 2025 Advance Insight
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    crop_product_ids = fields.Many2many(
        "product.product",
        "res_partner_product_harvest_crops_rel",
        "partner_id",
        "product_id",
        domain=[("crop_product", "=", True)],
        string="Crop Products",
    )

    @api.model
    def web_search_read(
        self, domain, specification, offset=0, limit=None, order=None, count_limit=None
    ):
        if self._context.get("filter_duplicate_phone"):
            self._cr.execute("""
                SELECT DISTINCT ptn1.id
                FROM res_partner ptn1
                INNER JOIN res_partner ptn2 ON ptn1.id != ptn2.id
                AND ptn1.phone = ptn2.phone
                WHERE ptn1.phone IS NOT NULL
            """)
            phone_duplicate_ids = [ptn[0] for ptn in self._cr.fetchall()]
            if domain:
                domain = ["&", ("id", "in", phone_duplicate_ids)] + domain
            else:
                domain = [("id", "in", phone_duplicate_ids)]
        return super().web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )
