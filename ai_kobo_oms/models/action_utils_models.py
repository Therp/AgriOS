# -*- coding: utf-8 -*-

from odoo import models, fields


class KoboInputFarmers(models.Model):
    _name = 'kobo.input.farmers'
    _description = 'Kobo Input Farmers'
    
    partner_ids = fields.Many2many('res.partner', 'kobo_input_farmers_partners_rel', 'input_farmers_id', 'partner_id', 'Input Farmers', readonly=True)
    input_id = fields.Many2one('kobo.asset.input', 'Kobo Input', required=True, ondelete='cascade', readonly=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name')
    
    def _compute_display_name(self):
        for kif in self:
            kif.display_name = f"Input Farmers {kif.id}"
    