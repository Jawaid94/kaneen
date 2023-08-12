# -*- coding: utf-8 -*-

from odoo import fields, models, _
from datetime import datetime
import datetime


class ImportStockInventoryLog(models.Model):
    _name = "ywt.import.stock.inventory.log"

    name = fields.Char(string="Name")
    log_date = fields.Datetime(string="Log Date")
    operation = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Operation")
    log_line_ids = fields.One2many("ywt.import.stock.inventory.log.line", "log_id", string="Log Line")

    def log_record(self, operation_type):
        sequence_id = self.env.ref('import_stock_inventory.stock_inventory_log_seq')
        if sequence_id:
            record_name = sequence_id.next_by_id()
        else:
            record_name = '/'
        log_vals = {
            'name': record_name,
            'log_date': datetime.datetime.now(),
            'operation': operation_type,

        }
        log_record = self.create(log_vals)

        return log_record

    def post_log_line(self, message, type='info'):
        self.ensure_one()
        log_line_obj = self.env['ywt.import.stock.inventory.log.line']
        log_line_vals = {
            'log_type': type,
            'log_id': self.id,
            'message': message,

        }
        log_line_obj.create(log_line_vals)


class ImportStockInventoryLogLine(models.Model):
    _name = "ywt.import.stock.inventory.log.line"
    _rec_name = "log_id"

    message = fields.Text(string="Message")
    log_type = fields.Selection([('info', 'Info'), ('mismatch', 'Mismatch')], string="Log Type")
    log_id = fields.Many2one('ywt.import.stock.inventory.log', string="Log ID")
