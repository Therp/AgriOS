from odoo import _, api, fields, models


class Farmer(models.Model):
    _inherit = "res.partner"

    farmer_requires_contract = fields.Boolean(
        "Requires Contract",
        tracking=True,
        default=False,
        help="If selected, this farmer will require a valid"
        " offtake agreement contract to sell inputs or to buy off-takes."
        " If unselected, no valid contract is needed for sales or purchases.",
    )
    total_contracted_acreage = fields.Float(compute="_compute_total_contracted_acreage")
    non_contracted_acreage = fields.Float(compute="_compute_non_contracted_acreage")
    # Linked Offtake Agreements
    count_farmer_contracts = fields.Integer(compute="_compute_count_farmer_contracts")
    farmer_contract_ids = fields.One2many("farmer.contract", "farmer_id", "Contracts")
    open_contract_ids = fields.One2many(
        "farmer.contract", string="Open Contracts", compute="_compute_open_contracts"
    )
    open_contract_input_ids = fields.One2many(
        "farmer.contract",
        string="Open Contracts [Input State]",
        compute="_compute_open_contracts",
    )
    open_contract_harvest_ids = fields.One2many(
        "farmer.contract",
        string="Open Contracts [Harvest State]",
        compute="_compute_open_contracts",
    )
    count_input_sales = fields.Integer(compute="_compute_count_input_sales")
    count_harvest_offtakes = fields.Integer(compute="_compute_count_harvest_offtakes")
    count_trainings = fields.Integer(compute="_compute_count_trainings")
    has_expired_contract = fields.Boolean(compute="_compute_has_expired_contract")
    can_order_inputs = fields.Boolean(
        "Can Order Inputs [Without Confirmation]", compute="_compute_can_order_inputs"
    )
    can_order_inputs_confirm = fields.Boolean(
        "Can Order Inputs [With Confirmation]", compute="_compute_can_order_inputs"
    )
    can_register_offtakes = fields.Boolean(
        "Can Register Offtakes [Without Confirmation]",
        compute="_compute_can_register_offtakes",
    )
    can_register_offtakes_confirm = fields.Boolean(
        "Can Register Offtakes [With Confirmation]",
        compute="_compute_can_register_offtakes",
    )
    unreconciled_aml_ids = fields.One2many(
        "account.move.line",
        compute="_compute_agrios_unreconciled_aml_ids",
        readonly=False,
    )  # copy of enterprise unreconciled_aml_ids

    @api.depends("invoice_ids")
    @api.depends_context("company", "allowed_company_ids")
    def _compute_agrios_unreconciled_aml_ids(self):
        AccountMoveLine = self.env["account.move.line"]
        for this in self:
            this.unreconciled_aml_ids = AccountMoveLine.search(
                [
                    ("partner_id", "=", this.id),
                    ("reconciled", "=", False),
                    ("account_id.deprecated", "=", False),
                    ("account_id.account_type", "=", "asset_receivable"),
                    ("parent_state", "=", "posted"),
                    ("company_id", "child_of", self.env.company.id),
                ]
            )

    @api.depends("farmer_stage", "farmer_requires_contract", "company_id")
    def _compute_can_order_inputs(self):
        for farmer in self:
            if farmer.farmer_stage == "verified":
                if farmer.open_contract_input_ids:
                    farmer.can_order_inputs = True
                    farmer.can_order_inputs_confirm = False
                elif farmer.open_contract_harvest_ids:
                    farmer.can_order_inputs_confirm = (
                        farmer.company_id or self.env.company
                    ).allow_operations_out_of_phase
                    farmer.can_order_inputs = (
                        not farmer.can_order_inputs_confirm
                        and not farmer.farmer_requires_contract
                    )
                else:
                    farmer.can_order_inputs = not farmer.farmer_requires_contract
                    farmer.can_order_inputs_confirm = False
            else:
                farmer.can_order_inputs = farmer.can_order_inputs_confirm = False

    @api.depends("farmer_stage", "farmer_requires_contract", "company_id")
    def _compute_can_register_offtakes(self):
        for farmer in self:
            if farmer.farmer_stage == "verified":
                if farmer.open_contract_harvest_ids:
                    farmer.can_register_offtakes = True
                    farmer.can_register_offtakes_confirm = False
                elif farmer.open_contract_input_ids:
                    farmer.can_register_offtakes_confirm = (
                        farmer.company_id or self.env.company
                    ).allow_operations_out_of_phase
                    farmer.can_register_offtakes = (
                        not farmer.can_register_offtakes_confirm
                        and not farmer.farmer_requires_contract
                    )
                else:
                    farmer.can_register_offtakes = not farmer.farmer_requires_contract
                    farmer.can_register_offtakes_confirm = False
            else:
                farmer.can_register_offtakes = farmer.can_register_offtakes_confirm = (
                    False
                )

    def _compute_has_expired_contract(self):
        for farmer in self:
            farmer.has_expired_contract = any(
                farmer.farmer_contract_ids.mapped("expired_contract")
            )

    def _compute_open_contracts(self):
        for farmer in self:
            farmer.open_contract_ids = farmer.farmer_contract_ids.filtered(
                lambda cont: cont.contract_stage == "open"
            )
            farmer.open_contract_input_ids = farmer.open_contract_ids.filtered(
                lambda cont: not cont.ready_for_harvest
            )
            farmer.open_contract_harvest_ids = farmer.open_contract_ids.filtered(
                lambda cont: cont.ready_for_harvest
            )

    def _compute_count_farmer_contracts(self):
        for rec in self:
            rec.count_farmer_contracts = self.env["farmer.contract"].search_count(
                [("farmer_id", "=", rec.id)]
            )

    def _compute_count_input_sales(self):
        for rec in self:
            rec.count_input_sales = self.env["sale.order"].search_count(
                [("partner_id", "=", rec.id)]
            )

    def _compute_count_harvest_offtakes(self):
        for rec in self:
            rec.count_harvest_offtakes = self.env["purchase.order"].search_count(
                [("partner_id", "=", rec.id)]
            )

    def _compute_total_contracted_acreage(self):
        for partner in self:
            partner.total_contracted_acreage = sum(
                partner.farmer_contract_ids.filtered(
                    lambda contract: contract.contract_stage == "open"
                ).mapped("contract_acreage")
            )

    def _compute_non_contracted_acreage(self):
        for rec in self:
            rec.non_contracted_acreage = (
                rec.total_acreage - rec.total_contracted_acreage
            )

    def _prepare_verify_farmer_vals(self):
        vals = super()._prepare_verify_farmer_vals()
        company = self.company_id or self.env.company
        vals["farmer_requires_contract"] = company.a_default_contract_required
        return vals

    def action_view_farmer_contracts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Offtake Agreements",
            "view_mode": "list,form",
            "res_model": "farmer.contract",
            "domain": [("farmer_id", "=", self.id)],
            "context": {
                "default_farmer_id": self.id,
                "default_company_id": self.company_id.id or self.env.company.id,
            },
            "help": _("""
                <p class="o_view_nocontent_smiling_face">
                    Create the first Offtake Agreement
                </p>
                <p>
                    Odoo helps you easily track all activities
                    related to an offtake agreement contract
                </p>
            """),
        }

    def action_view_agrios_sale_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Quotations & Sales",
            "view_mode": "list,form",
            "res_model": "sale.order",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "create": False,
            },
        }

    def action_view_agrios_purchase_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "RFQs and Purchases",
            "view_mode": "list,form",
            "res_model": "purchase.order",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "create": False,
            },
        }

    def action_create_agrios_so(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": self.display_name + " - " + _("Order Inputs"),
            "view_mode": "form",
            "res_model": "sale.order",
            "context": {
                "default_partner_id": self.id,
            },
        }
        if not self.farmer_requires_contract and self.crop_product_ids:
            allow_operations_out_of_phase = (
                self.company_id or self.env.company
            ).allow_operations_out_of_phase
            if not (
                self.open_contract_input_ids
                or (allow_operations_out_of_phase and self.open_contract_ids)
            ):
                input_products = (
                    self.crop_product_ids.mapped("seed_ids")
                    | self.crop_product_ids.mapped("seed_ids.related_inputs_ids")
                    | self.crop_product_ids.mapped("related_inputs_ids")
                )

                if input_products:
                    order_line_vals = []

                    for input_prd in input_products:
                        order_line_vals.append(
                            (
                                0,
                                0,
                                {
                                    "product_id": input_prd.id,
                                    "product_uom_qty": (
                                        self.total_acreage * input_prd.qty_per_acreage
                                    )
                                    or 1.0,
                                },
                            )
                        )

                    action["context"]["default_order_line"] = order_line_vals
        return action

    def action_create_agrios_po(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.display_name + " - " + _("Off-Take"),
            "view_mode": "form",
            "res_model": "purchase.order",
            "context": {
                "default_partner_id": self.id,
                "default_date_planned": fields.Datetime.now(),
            },
        }

    def get_offtake_estimate(self, crop_product):
        """Get the total estimate per acre"""
        self.ensure_one()
        estimated_yield = crop_product.estimated_yield
        if crop_product.harvest_product_type == "tree_crop":
            domain = [
                ("plot_id", "in", self.plot_ids.ids),
                ("product_id", "=", crop_product.id),
            ]
            subplots = self.env["farmer.plot.crop.area"].search(domain)
            if subplots:
                total_yield = sum(subplots.mapped("annual_estimated_yield"))
                total_acreage = sum(subplots.mapped("acreage"))

                if total_acreage > 0:
                    estimated_yield = total_yield / total_acreage
        return estimated_yield
