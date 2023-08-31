# -*- coding: iso-8859-1 -*-

from odoo import models, fields, api
from ..models.xml_rpc_request import connect


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    return_to_shatha = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        return_to_shatha = False
        shatha_partner_id = self.env['res.partner'].search([('name', '=', 'Shatha AlKhaleej')])
        if self._context.get('active_model') and self._context['active_model'] == 'stock.picking':
            sale_order_id = self.env['stock.picking'].browse(res['picking_id']).move_lines.sale_line_id.order_id
        else:
            sale_order_id = self.env['sale.order'].browse(self._context.get('sale_order_id', False))

        if sale_order_id:
            purchase_order_id = self.env['purchase.order'].search([('origin', 'like', sale_order_id.name)])
            if purchase_order_id and purchase_order_id.partner_id == shatha_partner_id:
                return_to_shatha = True

        res['return_to_shatha'] = return_to_shatha

        return res

    def create_returns(self):
        self = self.with_context(ignore_push_apply=True)
        res = super(StockReturnPicking, self).create_returns()

        stock_picking = self.env['stock.picking'].browse(res.get('res_id', False))
        stock_picking.write({'show_in_sale': True})
        if stock_picking:
            sale_order_id = self.env['sale.order'].browse(self._context.get('sale_order_id', False))
            purchase_order_id = self.env['purchase.order'].search([('origin', 'like', sale_order_id.name)])
            # sale_order_id._get_purchase_orders()

            if sale_order_id and sale_order_id.state != 'waiting_for_ret':
                sale_order_id.sudo().write({
                    'state': 'waiting_for_ret'
                })

            # sale_order_id.write({
            #     'state': 'item_returned'
            # })

            local_return_location = self.env['stock.location'].search(
                [('return_location', '=', True), ('barcode', '=', 'return')])
            # if sale_order_id.invoice_ids and sale_order_id.payment_status == 'paid':
            #     reversal_wizard = self.env['account.move.reversal'].create({
            #         'move_ids': [(6, 0, sale_order_id.invoice_ids.ids)],
            #         'date_mode': 'custom',
            #         'refund_method': 'refund',
            #         'journal_id': sale_order_id.invoice_ids[0].journal_id.id,
            #         'company_id': sale_order_id.company_id.id
            #     })
            #     reversal_move = reversal_wizard.reverse_moves()
            #     reversal_move = self.env['account.move'].browse(reversal_move.get('res_id', False))
            #     account_line = reversal_move.invoice_line_ids.filtered(
            #         lambda x: x.product_id.id not in self.product_return_moves.product_id.ids)
            #     reversal_move.write({
            #         "invoice_line_ids": [(2, i) for i in account_line.ids],
            #         "return_picking_id": stock_picking.id
            #     })
            #     for line in self.product_return_moves:
            #         reversal_move.invoice_line_ids.filtered(
            #             lambda x: x.product_id.id == line.product_id.id).with_context(
            #             check_move_validity=False).write({
            #             'quantity': line.quantity
            #         })
            #     sale_order_id._sale_order_payment_status()

            # individual picking type for putaway return
            internal_picking = stock_picking.copy({
                'picking_type_id': stock_picking.picking_type_id.picking_type_for_putaway.id or 3,
                # 'partner_id': shatha_partner_id.id,
                'location_id': stock_picking.location_dest_id.id,
                'location_dest_id': local_return_location.id
            })
            internal_picking.move_lines.write({
                'location_id': stock_picking.location_dest_id.id,
                'location_dest_id': local_return_location.id
            })
            for line in stock_picking.move_lines:
                line.write({
                    'move_dest_ids': [
                        (6, 0,
                         internal_picking.move_lines.filtered(lambda x: x.product_id.id == line.product_id.id).ids)]
                })
            internal_picking.action_confirm()

            if not purchase_order_id:
                # no purchase -> only return to stock
                return res

            vendor = purchase_order_id.partner_id
            vendor_location = vendor.property_stock_supplier

            # picking for vendor
            picking_to_vendor = stock_picking.copy({
                'picking_type_id': 2,
                'partner_id': vendor.id,
                'location_id': internal_picking.location_dest_id.id,
                'location_dest_id': vendor_location.id,
                'show_in_purchase': True,
                'show_in_sale': False
            })
            picking_to_vendor.move_lines.write({
                'location_id': internal_picking.location_dest_id.id,
                'location_dest_id': vendor_location.id,
            })
            for line in internal_picking.move_lines:
                line.write({
                    'move_dest_ids': [
                        (6, 0,
                         picking_to_vendor.move_lines.filtered(lambda x: x.product_id.id == line.product_id.id).ids)]
                })
            picking_to_vendor.action_confirm()

            if self.return_to_shatha:
                url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
                db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
                username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
                password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
                uid, models = connect(url, db, username, password)
                sale = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
                                         [[['client_order_ref', '=', purchase_order_id.name]]],
                                         {'fields': ['name', 'id', 'picking_ids']})
                if sale[0].get('picking_ids', False):
                    picking = models.execute_kw(db, uid, password, 'stock.picking', 'search_read',
                                                [[['id', '=', sale[0].get('picking_ids', False)[0]]]],
                                                {'fields': ['name', 'id', 'state']})
                    # location = models.execute_kw(db, uid, password, 'stock.location', 'search_read',
                    #                             [[]],
                    #                             {'fields': ['name', 'id', 'state']})
                    # if picking[0].get('state', False) == 'done':
                    vals_list = {
                        'picking_id': picking[0].get('id', False),
                        'location_id': 8
                    }
                    return_wizard = models.execute_kw(db, uid, password, 'stock.return.picking', 'create',
                                                      [vals_list])
                    for line in self.product_return_moves:
                        product = False
                        barcodes = []
                        if line.product_id.barcode:
                            barcodes.append(line.product_id.barcode)
                        if line.product_id.barcode_ids:
                            barcodes.extend(line.product_id.barcode_ids.mapped('name'))

                        if line.product_id.sku_shatha:
                            product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                    [[['default_code', '=', line.product_id.sku_shatha]]],
                                                    {'fields': ['name', 'id', 'product_variant_id']})
                        if not product:
                            product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                        [[['default_code', '=', line.product_id.default_code]]],
                                                        {'fields': ['name', 'id', 'product_variant_id']})
                        if not product and barcodes:
                            product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                        [[['barcode', 'in', barcodes]]],
                                                        {'fields': ['name', 'id', 'product_variant_id']})

                        # if line.product_id.sku_shatha:
                        #     product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                        #                                 [[['default_code', '=', line.product_id.sku_shatha]]],
                        #                                 {'fields': ['name', 'id', 'product_variant_id']})
                        # else:
                        #     product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                        #                                 [["|", ['default_code', '=', line.product_id.default_code], ['barcode', '=', line.product_id.barcode]]],
                        #                                 {'fields': ['name', 'id', 'product_variant_id']})

                        move_id = models.execute_kw(db, uid, password, 'stock.move', 'search_read',
                                                    [[['picking_id', '=', picking[0].get('id', False)],
                                                      ['product_id', '=', product[0]['product_variant_id'][0]]]],
                                                    {'fields': ['id', ]}
                                                    )

                        vals_list = {
                            'product_id': product[0]['product_variant_id'][0],
                            'quantity': line.quantity,
                            'wizard_id': return_wizard,
                            'move_id': move_id[0].get('id', False)
                        }
                        return_wizard_line = models.execute_kw(db, uid, password, 'stock.return.picking.line', 'create',
                                                               [vals_list])
                    return_wizard = models.execute_kw(db, uid, password, 'stock.return.picking', 'create_returns',
                                                      [return_wizard])
        return res
