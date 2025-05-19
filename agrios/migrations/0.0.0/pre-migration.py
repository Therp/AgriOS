# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'ai_agrios_fmis_tech';") # 'Uninstall' deprecated module ai_agrios_fmis_tech
    