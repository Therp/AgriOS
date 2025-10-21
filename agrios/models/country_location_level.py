from odoo import api, fields, models
from odoo.tools import ormcache


class CountryLocationLevel(models.Model):
    _name = "country.location.level"
    _description = "Country Area Level"
    _order = "country_id, level"

    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env.company.country_id,
    )
    level = fields.Integer(required=True, default=1)
    name = fields.Char("Designation", required=True)

    _sql_constraints = [
        (
            "unique_country_level",
            "UNIQUE(country_id, level)",
            "Country / level must be unique!",
        ),
        (
            "unique_country_name",
            "UNIQUE(country_id, name)",
            "Country / level designation must be unique!",
        ),
        (
            "check_level_value",
            "CHECK(level > 0 AND level < 7)",
            "Level needs to be between 1 and 6!",
        ),
    ]

    @ormcache("country_id")
    def _get_country_details(self, country_id):
        if country_id:
            self._cr.execute(
                "SELECT level, name FROM country_location_level WHERE country_id = %s",
                (country_id,),
            )
            loc_details = dict(self._cr.fetchall())
        else:
            loc_details = {}

        max_level = 0

        for level in range(1, 7):
            if level not in loc_details:
                loc_details[level] = "- Undefined -"
            elif level > max_level:
                max_level = level

        return loc_details, max_level

    @api.model_create_multi
    def create(self, vals_list):
        ret = super().create(vals_list)
        self.env.registry.clear_cache()
        return ret

    def write(self, vals):
        ret = super().write(vals)
        self.env.registry.clear_cache()
        return ret

    def unlink(self):
        ret = super().unlink()
        self.env.registry.clear_cache()
        return ret
