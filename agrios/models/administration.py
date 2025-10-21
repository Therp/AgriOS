from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AreaLevel6(models.Model):
    _name = "area.level.6"
    _description = "Area Level 6"
    _order = "country_id, name"

    name = fields.Char(required=True)
    manager_id = fields.Many2one("res.users", "Area Manager")
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "An area 6 with the same name already exists!"),
    ]


class AreaLevel5(models.Model):
    _name = "area.level.5"
    _description = "Area Level 5"
    _order = "country_id, name"

    name = fields.Char(required=True)
    manager_id = fields.Many2one("res.users", "Area Manager")
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    parent_id = fields.Many2one(
        "area.level.6", "Parent Area", domain="[('country_id','=',country_id)]"
    )
    active = fields.Boolean(default=True)
    is_parent_required = fields.Boolean(
        compute="_compute_is_parent_required", string="Parent Area Required"
    )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "An area 5 with the same name already exists!"),
    ]

    @api.depends("country_id")
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env[
                "country.location.level"
            ]._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 5


class AreaLevel4(models.Model):
    _name = "area.level.4"
    _description = "Area Level 4"
    _order = "country_id, name"

    name = fields.Char(required=True)
    manager_id = fields.Many2one("res.users", "Area Manager")
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    parent_id = fields.Many2one(
        "area.level.5", "Parent Area", domain="[('country_id','=',country_id)]"
    )
    active = fields.Boolean(default=True)
    is_parent_required = fields.Boolean(
        compute="_compute_is_parent_required", string="Parent Area Required"
    )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "An area 4 with the same name already exists!"),
    ]

    @api.depends("country_id")
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env[
                "country.location.level"
            ]._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 4


class Arealevel3(models.Model):  # AreaLevel3
    _name = "area.level.3"
    _description = "Area Level 3"
    _order = "country_id, name"

    name = fields.Char(required=True)
    manager_id = fields.Many2one("res.users", "Area Manager")
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    parent_id = fields.Many2one(
        "area.level.4", "Parent Area", domain="[('country_id','=',country_id)]"
    )
    active = fields.Boolean(default=True)
    is_parent_required = fields.Boolean(
        compute="_compute_is_parent_required", string="Parent Area Required"
    )

    _sql_constraints = [
        (
            "unique_region_name",
            "UNIQUE(name)",
            "An Area Level with this name already exists!",
        ),
    ]

    @api.depends("country_id")
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env[
                "country.location.level"
            ]._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 3


class Arealevel2(models.Model):  # AreaLevel2
    _name = "area.level.2"
    _description = "Area Level 2"
    _order = "country_id, name"

    name = fields.Char(required=True)
    parent_id = fields.Many2one(
        "area.level.3",
        "Parent Area",
        domain="[('country_id','=',country_id)]",
        ondelete="restrict",
    )
    manager_id = fields.Many2one("res.users", "Area Manager")
    active = fields.Boolean(default=True)

    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    is_parent_required = fields.Boolean(
        compute="_compute_is_parent_required", string="Parent Area Required"
    )

    _sql_constraints = [
        (
            "unique_loc_area_2_name",
            "UNIQUE(name)",
            "An Area Level with this name already Exists",
        ),
    ]

    @api.constrains("country_id", "parent_id")
    def _check_parent_required_if_country_requires_level2(self):
        cll_env = self.env["country.location.level"]
        for area in self:
            loc_details, max_level = cll_env._get_country_details(area.country_id.id)
            if max_level > 2 and not area.parent_id:
                raise ValidationError(
                    _(
                        "Parent Area is required for countries"
                        " that require Level 2 areas."
                    )
                )

    @api.depends("country_id")
    def _compute_is_parent_required(self):
        for record in self:
            loc_details, max_level = self.env[
                "country.location.level"
            ]._get_country_details(record.country_id.id)
            record.is_parent_required = max_level > 2

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if self._context.get("filter_regions"):
            filter_region_ids = self._context["filter_regions"]
            if filter_region_ids:
                if not domain:
                    domain = []
                domain = [["parent_id", "in", filter_region_ids]] + domain
        return super()._name_search(
            name, domain=domain, operator=operator, limit=limit, order=order
        )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get("filter_regions"):
            filter_region_ids = self._context["filter_regions"]
            if filter_region_ids:
                if not domain:
                    domain = []
                domain = [["parent_id", "in", filter_region_ids]] + domain
        return super().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )


class AreaLevel1(models.Model):  # AreaLevel1
    _name = "area.level.1"
    _description = "Area Level 1"
    _order = "country_id, name, parent_id"

    name = fields.Char(required=True)
    parent_id = fields.Many2one(
        "area.level.2",
        "Parent Area",
        domain="[('country_id','=',country_id)]",
        ondelete="restrict",
    )
    active = fields.Boolean(default=True)
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )

    farmer_group_ids = fields.One2many(
        "farmer.group", "loc_area_1_id", "Farmer Groups", readonly=True, copy=False
    )
    manager_id = fields.Many2one("res.users", "Area Manager")

    _sql_constraints = [
        (
            "unique_level_1_level_3_combination",
            "UNIQUE(name, loc_area_2_id)",
            "An Area Level with this name already Exists in the specified Area Level 2",
        ),
    ]

    @api.constrains("country_id", "parent_id")
    def _check_parent_required_if_country_requires_level2(self):
        cll_env = self.env["country.location.level"]
        for area in self:
            loc_details, max_level = cll_env._get_country_details(area.country_id.id)
            if max_level > 1 and not area.parent_id:
                raise ValidationError(
                    _(
                        "Parent Area is required for countries"
                        " that require Level 2 areas."
                    )
                )

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if self._context.get("filter_loc_area_2s"):
            filter_loc_area_2_ids = self._context["filter_loc_area_2s"]
            if filter_loc_area_2_ids:
                if not domain:
                    domain = []
                domain = [["loc_area_2_id", "in", filter_loc_area_2_ids]] + domain

        return super()._name_search(
            name, domain=domain, operator=operator, limit=limit, order=order
        )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get("filter_loc_area_2s"):
            filter_loc_area_2_ids = self._context["filter_loc_area_2s"]
            if filter_loc_area_2_ids:
                if not domain:
                    domain = []
                domain = [["loc_area_2_id", "in", filter_loc_area_2_ids]] + domain

        return super().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )
