# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import wizards


def post_init_hook(env):
    # set fiscal country to kenya
    kenya = env["res.country"].search([("code", "=", "KE")], limit=1)
    if kenya:  # set units of measure to True by default
        env["res.config.settings"].create(
            {
                "group_uom": True,
                "group_auto_done_setting": True,
                "lock_confirmed_po": True,
                "account_fiscal_country_id": kenya.id,
            }
        ).execute()

    # Verify farmer records so they get the id
    env["res.partner"].search([("is_farmer", "=", True)]).verify_farmer()
