# -*- coding: utf-8 -*-

def migrate(cr, version):
    # ------------- certifying_organisation char field converted into many2one link res_partner with new name certifying_organisation_id -------------
    cr.execute("SELECT id, certifying_organisation FROM certification_type WHERE certifying_organisation IS NOT NULL AND certifying_organisation_id IS NULL;")
    for ctype_id, certifying_organisation in cr.fetchall():
        certifying_organisation = certifying_organisation.strip()
        if certifying_organisation:
            cr.execute("SELECT id FROM res_partner WHERE name ILIKE %s LIMIT 1;", (certifying_organisation,))
            ptn = cr.fetchone()
            if ptn and ptn[0]:
                certifying_organisation_id = ptn[0]
            else:
                cr.execute("""
                    INSERT INTO res_partner (name, display_name, create_date, create_uid, write_uid, lang, type, active, is_company, partner_share, write_date, picking_warn, purchase_warn, sale_warn, followup_reminder_type, outgrower_stage)
                    VALUES (%s, %s, NOW()::TIMESTAMP WITHOUT TIME ZONE, 1, 1, 'en_GB', 'contact', FALSE, TRUE, TRUE, NOW()::TIMESTAMP WITHOUT TIME ZONE, 'no-message', 'no-message', 'no-message', 'automatic', 'draft')
                    RETURNING id;""", (certifying_organisation, certifying_organisation))
                certifying_organisation_id = cr.fetchone()[0]
            cr.execute("UPDATE certification_type SET certifying_organisation_id = %s WHERE id = %s;", (certifying_organisation_id, ctype_id))
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    
    cr.execute("UPDATE res_partner SET is_farmer_trainer = TRUE WHERE id IN (SELECT DISTINCT trainer_id FROM farmer_training);") # set new flag is_farmer_trainer on partners as trainers on farmer_training
    
    # ------------- update posted farmers sequence ---------------------------------------------------------------------------------------------------
    cr.execute("SELECT id, number_next FROM ir_sequence WHERE code = 'outgrower.farmer'")
    farmer_sequence_tpl = cr.fetchone()
    if farmer_sequence_tpl and farmer_sequence_tpl[0]:
        farmer_sequence_id, farmer_sequence_number_next = farmer_sequence_tpl
        
        cr.execute("SELECT id FROM res_partner WHERE outgrower_stage = 'verified' AND (outgrower_ref IS NULL OR outgrower_ref = '/') ORDER BY id ASC")
        partner_ids = [p[0] for p in cr.fetchall()]
        if partner_ids:
            for partner_id in partner_ids:
                partner_sequence = ('OF' + ('%05d' % farmer_sequence_number_next))
                cr.execute("UPDATE res_partner SET outgrower_ref = %s WHERE id = %s", (partner_sequence, partner_id))
                farmer_sequence_number_next += 1
            
            cr.execute("UPDATE ir_sequence SET number_next = %s WHERE id = %s", (farmer_sequence_number_next, farmer_sequence_id))
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    
    # ------------- update posted contracts sequence ---------------------------------------------------------------------------------------------------
    cr.execute("SELECT id, number_next FROM ir_sequence WHERE code = 'offtake.agreement'")
    contract_sequence_tpl = cr.fetchone()
    if contract_sequence_tpl and contract_sequence_tpl[0]:
        contract_sequence_id, contract_sequence_number_next = contract_sequence_tpl
        
        cr.execute("SELECT id FROM offtake_agreement WHERE contract_stage IN ('open','closed') AND (name IS NULL OR name = '/') ORDER BY id ASC")
        contract_ids = [p[0] for p in cr.fetchall()]
        if contract_ids:
            for contract_id in contract_ids:
                contracts_sequence = ('OA' + ('%05d' % contract_sequence_number_next))
                cr.execute("UPDATE offtake_agreement SET name = %s WHERE id = %s", (contracts_sequence, contract_id))
                contract_sequence_number_next += 1
            
            cr.execute("UPDATE ir_sequence SET number_next = %s WHERE id = %s", (contract_sequence_number_next, contract_sequence_id))
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    