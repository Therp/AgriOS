# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'ai_oms_fmis_tech';") # 'Uninstall' deprecated module ai_oms_fmis_tech
    