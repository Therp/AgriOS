# -*- coding: utf-8 -*-

from . import models
from . import wizard

def uninstall_hook(env):
    env.cr.execute("DELETE FROM ir_model_constraint WHERE name = 'res_partner_land_area_uom_fkey'")
    env.cr.execute("DELETE FROM ir_model_constraint WHERE name = 'res_config_settings_land_area_uom_fkey'")
    env.cr.execute("DELETE FROM ir_config_parameter WHERE key = 'farmer_management.land_area_uom'")