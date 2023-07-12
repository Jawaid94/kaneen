# -*- coding: iso-8859-1 -*-
import base64
import io
import csv

from odoo import models, fields, api


class ReturnWizard(models.TransientModel):
    _name = 'return.wizard'

    file = fields.Binary()

    def import_file(self):
        csv_data = base64.b64decode(self.file)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter=',')
        file_reader.extend(csv_reader)
        file_reader.pop(0)
        returns = set()
        broke_lines = []
        for count, line in enumerate(file_reader[0:]):
            if not line:
                break
            order = line[0].split("_")[1]
            quantity = int(line[7])
            product_name = line[6]
            product_sku = line[5]
            return_reason = line[9]

            stock_return = self.env['stock.return.picking']
            stock_return_line = self.env['stock.return.picking.line']
            order_id = self.env['sale.order'].search([('name', '=', order)])

            if order_id and order_id.state != 'waiting_for_ret':
                order_id.sudo().write({
                    'state': 'waiting_for_ret'
                })

            picking_id = order_id.picking_ids.filtered(
                lambda x: x.picking_type_code == 'outgoing' and x.state == 'done')
            move_id = picking_id.move_lines.filtered(lambda x: x.product_id.default_code == product_sku)
            location = self.env['stock.location'].search([('barcode', '=', 'WH-INPUT')])
            if order_id and move_id and location:
                # wizard = stock_return.search([('picking_id', '=', picking_id.id), ('return_to_shatha', '=', True)])
                wizard = stock_return.search([('picking_id', '=', picking_id.id)])
                if not wizard:
                    defaults = wizard.with_context(sale_order_id=order_id.id).default_get(['return_to_shatha'])
                    wizard = stock_return.create({
                        'picking_id': picking_id.id,
                        'location_id': location.id,
                        'return_to_shatha': defaults['return_to_shatha']
                    })

                returns.add(wizard.with_context(default_picking_id=picking_id.id, sale_order_id=order_id.id))
                # wizard_line = stock_return_line.search(
                #     [('product_id', '=', move_id.product_id.id), ('move_id', '=', move_id.id)])
                # if not wizard_line:
                wizard_line = stock_return_line.create({
                    'product_id': move_id.product_id.id,
                    'quantity': quantity,
                    'wizard_id': wizard.id,
                    'move_id': move_id.id,
                    'return_comment': return_reason
                })
            else:
                broke_lines.append(str(count + 1))

        for wizard in returns:
            wizard.create_returns()

            wizard.product_return_moves.sudo().unlink()
            wizard.sudo().unlink()

        if broke_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': "Some lines don't import, pleas check it {}".format(', '.join(broke_lines)),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': "Returns successfully created",
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
