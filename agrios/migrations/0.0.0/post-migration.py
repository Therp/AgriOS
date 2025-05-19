# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("DELETE FROM ir_module_module WHERE name = 'ai_agrios_fmis_tech';") # Delete module record of deprecated module ai_agrios_fmis_tech
    