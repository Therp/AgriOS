# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("ALTER TABLE farmer_group RENAME COLUMN chairperson TO chairperson_id;") # Rename column that was changed
    cr.execute("ALTER TABLE farmer_group RENAME COLUMN group_sec TO group_sec_id;") # Rename column that was changed
    cr.execute("ALTER TABLE farmer_group RENAME COLUMN group_treasurer TO group_treasurer_id;") # Rename column that was changed
    
    cr.execute("ALTER TABLE certified_farmer RENAME TO farmer_certification;") # Rename table name that was changed
    
    cr.execute("DELETE FROM ir_ui_view WHERE name = 'view.oms.res.config.settings.form';") # Delete AgriOS configurations view to be recreated again to avoid conflicts
    