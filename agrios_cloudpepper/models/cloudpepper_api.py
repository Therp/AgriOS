# -*- coding: utf-8 -*-

import json
import logging
import requests

from odoo import models, fields, api, _, release
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CloudpepperClient(models.TransientModel):
    _name = 'cloudpepper.client'
    _description = 'Cloudpepper API Client (transient)'
    
    api_url = fields.Char(required=True)
    api_key = fields.Char(required=True)
    
    @api.model
    def get_client(self):
        conf_env = self.env['ir.config_parameter'].sudo()
        api_url = conf_env.get_param('cloudpepper.api_url')
        api_key = conf_env.get_param('cloudpepper.api_key')
        
        if api_url and api_key:
            return self.sudo().create({
                'api_url': api_url,
                'api_key': api_key,
            })
        else:
            return None
    
    def list_servers(self):
        """GET /servers"""
        return self._request('GET', '/servers')
    
    def list_instances(self):
        """GET /instances"""
        return self._request('GET', '/instances')
    
    def create_instance(self, server_id, instance_name, instance_url, odoo_version=None):
        """POST /instances"""
        payload = {
            "serverId": server_id,
            "config": {
                "name": instance_name,
                "domain": instance_url,
                "odoo_version": odoo_version or release.major_version,
            }
        }
        return self._request('POST', '/instances', payload=payload)
    
    def add_module(self, instance_id, repo, branch, repo_type, module_name):
        """
        Add a module to an instance
        :param instance_id:
        :param repo:
        :param branch:
        :param repo_type:
        :param module_name:
        :return:
        """
        payload = {
            "repo": repo,
            "branch": branch,
            "type": repo_type,
            "init": module_name,
        }
        return self._request('POST', f'/instances/{instance_id}/modules', payload=payload)
    
    def get_instance_config(self, instance_id):
        """GET /instances/{id}/config → returns the Odoo config for that instance."""
        return self._request('GET', f'/instances/{instance_id}/config')
    
    def get_server_stats(self, server_id):
        """GET /servers/{id}/stats"""
        return self._request('GET', f'/servers/{server_id}/stats')
    
    def install_modules(self, instance_id, git_repos):
        """
        POST /instances/{id}/modules
        git_repos: list of {"url": "...", "branch": "..."}
        """
        return self._request('POST', f'/instances/{instance_id}/modules', payload={"modules": git_repos})
    
    def list_installed_modules(self, instance_id):
        """GET /instances/{id}/installed-modules → returns list of installed Odoo addons."""
        return self._request('GET', f'/instances/{instance_id}/installed-modules')
    
    def list_users(self, instance_id):
        """GET /instances/{id}/installed-modules → returns list of installed Odoo addons."""
        return self._request('GET', f'/instances/{instance_id}/installed-modules')
    
    def _request(self, method, endpoint, payload=None, params=None):
        """
        Core request method.
          - GETs send params, no body.
          - Others send JSON body.
        """
        base_url = self.api_url.rstrip('/')
        url = f"{base_url}{endpoint}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

        _logger.debug("Cloudpepper API → %s %s headers=%s params=%s payload=%s",
                      method, url, headers, params or payload, payload)
        try:
            if method.upper() == 'GET':
                resp = requests.get(url, headers=headers, params=params or payload, timeout=30)
            
            else:
                headers['Content-Type'] = 'application/json'
                resp = requests.request(method, url, headers=headers, json=payload or {}, timeout=30)
            
            _logger.debug("Cloudpepper API ← %s %s\n%s", resp.status_code, resp.url, resp.text)
            
            resp.raise_for_status() # Raise for HTTP errors (4xx/5xx)
            
            try:
                return resp.json()
            
            except ValueError: # Fallback: manually load from text
                try:
                    return json.loads(resp.text)
                
                except ValueError:  # Not JSON after all: return raw text
                    return resp.text
        
        except requests.HTTPError as e:
            # Try to extract JSON error message
            try:
                err = resp.json()
            except Exception:
                err = resp.text or str(e)
            msg = _("Cloudpepper API [%s %s] failed (%s):\n%s") % (
                method, endpoint, resp.status_code, err)
            _logger.error(msg, exc_info=True)
            raise UserError(msg)
        
        except requests.RequestException as e:
            _logger.error("Cloudpepper API request error", exc_info=True)
            raise UserError(_("Cloudpepper API request failed:\n%s") % e)
    