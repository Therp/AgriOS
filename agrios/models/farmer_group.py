from odoo import api, fields, models

FARMER_DOMAIN = (
    "[('is_farmer','=',True),"
    "('farmer_group_id','=',id),"
    "('farmer_stage','=','verified')]"
)


class FarmerGroup(models.Model):
    _name = "farmer.group"
    _description = "Farmer Group"
    _order = "name, loc_area_1_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    loc_area_1_id = fields.Many2one(
        "area.level.1", string="Area Level 1", tracking=True, required=True
    )
    loc_area_2_id = fields.Many2one(
        "area.level.2", "Area Level 2", ondelete="restrict", tracking=True
    )
    loc_area_3_id = fields.Many2one(
        "area.level.3", "Area Level 3", ondelete="restrict", tracking=True
    )
    loc_area_4_id = fields.Many2one(
        "area.level.4", "Area Level 4", ondelete="restrict", tracking=True
    )
    loc_area_5_id = fields.Many2one(
        "area.level.5", "Area Level 5", ondelete="restrict", tracking=True
    )
    loc_area_6_id = fields.Many2one(
        "area.level.6", "Area Level 6", ondelete="restrict", tracking=True
    )

    loc_area_1_label = fields.Char(
        "Area Level 1 Label", compute="_compute_loc_area_details"
    )
    loc_area_2_label = fields.Char(
        "Area Level 2 Label", compute="_compute_loc_area_details"
    )
    loc_area_3_label = fields.Char(
        "Area Level 3 Label", compute="_compute_loc_area_details"
    )
    loc_area_4_label = fields.Char(
        "Area Level 4 Label", compute="_compute_loc_area_details"
    )
    loc_area_5_label = fields.Char(
        "Area Level 5 Label", compute="_compute_loc_area_details"
    )
    loc_area_6_label = fields.Char(
        "Area Level 6 Label", compute="_compute_loc_area_details"
    )
    loc_area_max_level = fields.Integer(
        "Max Area Level", compute="_compute_loc_area_details"
    )

    country_id = fields.Many2one(
        "res.country",
        "Country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    manager_id = fields.Many2one(related="loc_area_1_id.manager_id")

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )

    chairperson_id = fields.Many2one(
        "res.partner",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    group_sec_id = fields.Many2one(
        "res.partner",
        "Secretary",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    group_treasurer_id = fields.Many2one(
        "res.partner",
        "Treasurer",
        tracking=True,
        domain=FARMER_DOMAIN,
    )
    member_ids = fields.One2many(
        "res.partner",
        "farmer_group_id",
        domain=[("is_farmer", "=", True), ("farmer_stage", "=", "verified")],
    )

    total_due = fields.Monetary(
        "Group Amount Due",
        compute="_compute_total_due",
        help="Sum amount due of all the group members",
    )

    _sql_constraints = [
        (
            "unique_group_loc_area_1_combination",
            "UNIQUE(name, loc_area_1_id)",
            "A Group with this name already Exists in the specified Area Level 1",
        )
    ]

    def init(self):
        result = super().init()
        self._cr.execute("""
            UPDATE farmer_group
            SET loc_area_2_id = ll1.parent_id
            FROM area_level_1 ll1
            WHERE farmer_group.loc_area_1_id = ll1.id
            AND farmer_group.loc_area_2_id IS NULL;

            UPDATE farmer_group
            SET loc_area_3_id = ll2.parent_id
            FROM area_level_2 ll2
            WHERE farmer_group.loc_area_2_id = ll2.id
            AND farmer_group.loc_area_2_id IS NULL;
        """)
        return result

    @api.depends("member_ids")
    def _compute_total_due(self):
        for farm_group in self:
            farm_group.total_due = 0.0
            for member in farm_group.member_ids:
                for aml in member.unreconciled_aml_ids:
                    if aml.company_id == farm_group.company_id and not aml.blocked:
                        farm_group.total_due += aml.amount_residual

    @api.depends("country_id")
    def _compute_loc_area_details(self):
        cll_env = self.env["country.location.level"]
        for farmer in self:
            loc_details, max_level = cll_env._get_country_details(farmer.country_id.id)
            farmer.loc_area_1_label = loc_details[1]
            farmer.loc_area_2_label = loc_details[2]
            farmer.loc_area_3_label = loc_details[3]
            farmer.loc_area_4_label = loc_details[4]
            farmer.loc_area_5_label = loc_details[5]
            farmer.loc_area_6_label = loc_details[6]
            farmer.loc_area_max_level = max_level

    @api.onchange("farmer_group_id")
    def _onchange_farmer_group(self):
        if self.farmer_group_id.loc_area_1_id:
            self.loc_area_1_id = self.farmer_group_id.loc_area_1_id

    @api.onchange("loc_area_1_id")
    def _onchange_loc_area_1_id(self):
        if self.loc_area_1_id:
            self.loc_area_2_id = self.loc_area_1_id.parent_id

    @api.onchange("loc_area_2_id")
    def _onchange_loc_area_2_id(self):
        if self.loc_area_2_id:
            self.loc_area_3_id = self.loc_area_2_id.parent_id

            if (
                self.loc_area_1_id
                and self.loc_area_1_id.parent_id != self.loc_area_2_id
            ):
                self.loc_area_1_id = False

    @api.onchange("loc_area_3_id")
    def _onchange_region_id(self):
        if self.loc_area_3_id:
            self.loc_area_4_id = self.loc_area_3_id.parent_id

            if (
                self.loc_area_2_id
                and self.loc_area_2_id.parent_id != self.loc_area_3_id
            ):
                self.loc_area_2_id = False
                self.loc_area_1_id = False

    @api.onchange("loc_area_4_id")
    def _onchange_loc_area_4_id(self):
        if self.loc_area_4_id:
            self.loc_area_5_id = self.loc_area_4_id.parent_id

            if (
                self.loc_area_3_id
                and self.loc_area_3_id.parent_id != self.loc_area_4_id
            ):
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False

    @api.onchange("loc_area_5_id")
    def _onchange_loc_area_5_id(self):
        if self.loc_area_5_id:
            self.loc_area_6_id = self.loc_area_5_id.parent_id

            if (
                self.loc_area_4_id
                and self.loc_area_4_id.parent_id != self.loc_area_5_id
            ):
                self.loc_area_4_id = False
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False

    @api.onchange("loc_area_6_id")
    def _onchange_loc_area_6_id(self):
        if self.loc_area_6_id:
            if (
                self.loc_area_5_id
                and self.loc_area_5_id.parent_id != self.loc_area_6_id
            ):
                self.loc_area_5_id = False
                self.loc_area_4_id = False
                self.loc_area_3_id = False
                self.loc_area_2_id = False
                self.loc_area_1_id = False

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)

        if view_type == "list" and view == self.env.ref(
            "agrios.view_farmer_group_tree", raise_if_not_found=False
        ):
            company_country_id = self.env.company.country_id.id
            loc_details, max_level = self.env[
                "country.location.level"
            ]._get_country_details(company_country_id)

            lev6 = arch.xpath("//field[@name='loc_area_6_id']")[0]
            if max_level >= 6:
                lev6.set("string", loc_details[6])
            else:
                lev6.getparent().remove(lev6)

            lev5 = arch.xpath("//field[@name='loc_area_5_id']")[0]
            if max_level >= 5:
                lev5.set("string", loc_details[5])
            else:
                lev5.getparent().remove(lev5)

            lev4 = arch.xpath("//field[@name='loc_area_4_id']")[0]
            if max_level >= 4:
                lev4.set("string", loc_details[4])
            else:
                lev4.getparent().remove(lev4)

            lev3 = arch.xpath("//field[@name='loc_area_3_id']")[0]
            if max_level >= 3:
                lev3.set("string", loc_details[3])
            else:
                lev3.getparent().remove(lev3)

            lev2 = arch.xpath("//field[@name='loc_area_2_id']")[0]
            if max_level >= 2:
                lev2.set("string", loc_details[2])
            else:
                lev2.getparent().remove(lev2)

            arch.xpath("//field[@name='loc_area_1_id']")[0].set(
                "string", loc_details[1]
            )
        return arch, view
