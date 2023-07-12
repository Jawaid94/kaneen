# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from .xml_rpc_request import connect


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xml_url = fields.Char(config_parameter='mo_kaneen.xml_url')
    xml_dbname = fields.Char(config_parameter='mo_kaneen.xml_dbname')
    xml_username = fields.Char(config_parameter='mo_kaneen.xml_username')
    xml_password = fields.Char(config_parameter='mo_kaneen.xml_password')
    responsible_user_id = fields.Many2one('res.users', config_parameter='mo_kaneen.responsible_user_id')
    shatha_write_date_product = fields.Datetime(config_parameter='mo_kaneen.shatha_write_date_product')
    shatha_write_date_quant = fields.Datetime(config_parameter='mo_kaneen.shatha_write_date_quant')
    shatha_location_id = fields.Many2one('stock.location', config_parameter='mo_kaneen.shatha_location_id')
    shatha_remote_contact_id = fields.Integer(config_parameter='mo_kaneen.shatha_remote_contact_id')
    shatha_remote_stock_location_id = fields.Integer(string="Shatha Remote Stock Location", config_parameter='mo_kaneen.shatha_remote_stock_location_id')

    def test_connect(self):
        uid, models = connect(self.xml_url, self.xml_dbname, self.xml_username, self.xml_password)
        if not uid:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': ("Connection not established"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ("Connection successfully established"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
