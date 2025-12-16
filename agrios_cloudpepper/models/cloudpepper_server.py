# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CloudpepperServer(models.Model):
    _name = 'cloudpepper.server'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cloudpepper Server'
    _order = 'name'

    name = fields.Char(readonly=True)
    server_id = fields.Char(string='Server ID', readonly=True)
    region = fields.Char(readonly=True)
    plan = fields.Char(readonly=True)
    status = fields.Selection([
        ('creating', 'Creating'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('deleted', 'Deleted'),
        ('available', 'Available'),
    ], readonly=True)
    created_at = fields.Datetime(string='Created At', readonly=True)
    cpu_usage = fields.Float(string='CPU Usage (%)', compute='_compute_server_stats', readonly=True)
    memory_usage = fields.Float(string='Memory Usage (%)', readonly=True)
    disk_usage = fields.Float(string='Disk Usage (%)', readonly=True)
    last_stats_update = fields.Datetime(string='Stats Updated', readonly=True)
    instance_ids = fields.One2many(
        'cloudpepper.instance', 'server_id',
        string='Odoo Instances', readonly=True)

    @api.depends_context('uid')
    def _compute_server_stats(self):
        cpu_usage, memory_usage, disk_usage = self._get_server_stats()
        for instance in self:
            instance.cpu_usage = cpu_usage
            instance.memory_usage = memory_usage
            instance.disk_usage = disk_usage

    def action_fetch_servers(self):
        """Sync all servers from the API into local records."""
        client = self.env['cloudpepper.client'].get_client()
        if client:
            try:
                data = client.list_servers()
            except UserError as e:
                raise
            for srv in data:
                vals = {
                    'name': srv.get('name'),
                    'server_id': srv.get('id'),
                    'region': srv.get('region'),
                    'plan': srv.get('plan'),
                    'status': srv.get('status'),
                    'created_at': srv.get('created_at'),
                }
                rec = self.search([('server_id', '=', srv.get('id'))], limit=1)
                if rec:
                    rec.write(vals)
                else:
                    self.create(vals)

    def action_update_stats(self):
        """Fetch and update server stats from Cloudpepper API."""
        self.ensure_one()
        cpu_usage, memory_usage, disk_usage = self._get_server_stats()
        vals = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'last_stats_update': fields.Datetime.now(),
        }

        self.write(vals)
        self.message_post(body=(
            f"Stats updated: CPU {vals['cpu_usage']}%, "
            f"Memory {vals['memory_usage']}%, Disk {vals['disk_usage']}%"
        ))

    def _get_server_stats(self):
        """ Fetch Server Usage on stats"""
        client = self.env['cloudpepper.client'].get_client()
        raw = client.get_server_stats(self.server_id)

        cpu_val = float(
            raw.get('cpu', {}) \
                .get('result', {}) \
                .get('value', [None, 0])[1]
        )

        mem = raw.get('mem', {})
        mem_avail = float(
            mem.get('node_memory_MemAvailable_bytes', {}) \
                .get('value', [None, 0])[1]
        )
        mem_total = float(
            mem.get('node_memory_MemTotal_bytes', {}) \
                .get('value', [None, 1])[1]
        ) or 1
        mem_val = ((mem_total - mem_avail) / mem_total) * 100

        disk = raw.get('disk', {})
        disk_free = float(
            disk.get('node_filesystem_free_bytes', {}) \
                .get('value', [None, 0])[1]
        )
        disk_total = float(
            disk.get('node_filesystem_size_bytes', {}) \
                .get('value', [None, 1])[1]
        ) or 1
        disk_val = ((disk_total - disk_free) / disk_total) * 100

        cpu_usage = round(cpu_val, 2),
        memory_usage = round(mem_val, 2)
        disk_usage = round(disk_val, 2)

        return cpu_usage[0], memory_usage, disk_usage
    