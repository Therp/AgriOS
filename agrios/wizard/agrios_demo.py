# -*- coding: utf-8 -*-

from odoo import models
from odoo.addons.base.models.ir_module import assert_log_admin_access
from odoo.modules.loading import load_data
from odoo.modules.graph import Graph
from odoo.modules.module import get_manifest
from odoo.exceptions import UserError

class AgriosDemo(models.TransientModel):

    _name = 'agrios.demo'
    _description = 'Agrios Demo'

    @assert_log_admin_access
    def action_load_demo_for_agrios(self):
        self.ensure_one()
        env = self.env(su=True)
        currency = self.env['res.currency'].search([('name', '=', 'KES')], limit=1)
        if  currency:
            self.env.company.write({'currency_id': currency.id})

        company = self.env.company
        company.write({'currency_id': currency.id})
        info = get_manifest('agrios')
        graph = Graph()
        node = graph.add_node('agrios', info)
        graph.update_from_db(env.cr)
        node.demo = True
        load_data(env, {}, 'init', kind='demo', package=node)

        env.clear()
        env['res.groups']._update_user_groups_view()
        env['res.partner'].search([('is_farmer', '=', True)]).verify_farmer()

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/odoo',
        }