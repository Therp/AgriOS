# -*- coding: utf-8 -*-

from . import models
from . import wizard

def uninstall_hook(env):
    env.cr.execute("DELETE FROM ir_model_constraint WHERE name = 'res_partner_land_area_uom_fkey'")
    env.cr.execute("DELETE FROM ir_model_constraint WHERE name = 'res_config_settings_land_area_uom_fkey'")
    env.cr.execute("DELETE FROM ir_config_parameter WHERE key = 'farmer_management.land_area_uom'")

def post_init_hook(env):
    # set fiscal country to kenya
    kenya = env['res.country'].search([('code', '=', 'KE')], limit=1)
    if kenya:        # set units of measure to True by default
        env['res.config.settings'].create({
            'group_uom': True,
            'group_auto_done_setting': True,
            'lock_confirmed_po': True,
            'account_fiscal_country_id': kenya.id,
        }).execute()

    # Verify farmer records so they get the id
    env['res.partner'].search([('is_farmer', '=', True)]).verify_farmer()


