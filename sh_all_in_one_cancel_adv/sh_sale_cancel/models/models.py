# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_stock_installed(self):
        stock_app = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'stock')], limit=1)
        if stock_app.state != 'installed':
            return False
        else:
            return True

    def _check_stock_account_installed(self):
        stock_account_app = self.env['ir.module.module'].sudo().search([('name','=','stock_account')],limit=1)
        if stock_account_app.state != 'installed':
            return False
        else:
            return True

    def action_sale_cancel(self):
        for rec in self:
            if rec.company_id.cancel_delivery and self._check_stock_installed():

                if rec.sudo().mapped('picking_ids'):
                    if rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        rec.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'cancel'})
                        rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'cancel'})
                    rec._sh_unreseve_qty()
                    rec.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'cancel'})

                    if rec._check_stock_account_installed():
                        
                        # cancel related accouting entries
                        account_move = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                        account_move_line_ids = account_move.sudo().mapped('line_ids')
                        reconcile_ids = []
                        if account_move_line_ids:
                            reconcile_ids = account_move_line_ids.sudo().mapped('id')
                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                        account_move.sudo().write({'state':'draft','name':'/'})
                        account_move.sudo().with_context({'force_delete':True}).unlink()
                        
                        # cancel stock valuation
                        stock_valuation_layer_ids = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                        if stock_valuation_layer_ids:
                            stock_valuation_layer_ids.sudo().unlink()

            if rec.company_id.cancel_invoice:
                if rec.mapped('invoice_ids'):
                    if rec.mapped('invoice_ids'):
                        move = rec.mapped('invoice_ids')
                        move_line_ids = move.sudo().mapped('line_ids')
                        reconcile_ids = []
                        if move_line_ids:
                            reconcile_ids = move_line_ids.sudo().mapped('id')
                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        payments = False
                        if reconcile_lines:
                            payments = self.env['account.payment'].search(['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                                'credit_move_id').ids), ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])

                            reconcile_lines.sudo().unlink()

                            if payments:

                                payment_ids = payments
                                if payment_ids.sudo().mapped('move_id').mapped('line_ids'):
                                    payment_lines = payment_ids.sudo().mapped('move_id').mapped('line_ids')
                                    reconcile_ids = payment_lines.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        move.mapped(
                            'line_ids.analytic_line_ids').sudo().unlink()

                        move_line_ids.sudo().write({'parent_state': 'draft'})
                        move.sudo().write({'state': 'draft'})

                        if payments:
                            payment_ids = payments
                            payment_ids.sudo().mapped(
                                'move_id').write({'state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped(
                                'line_ids').sudo().write({'parent_state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                            payment_ids.sudo().write({'state': 'cancel'})

                            payment_ids.sudo().mapped('move_id').with_context(
                                {'force_delete': True}).unlink()

                    rec.mapped('invoice_ids').sudo().write({'state': 'cancel'})
            rec.sudo().write({'state': 'cancel'})

    def action_sale_cancel_draft(self):
        for rec in self:
            if rec.company_id.cancel_delivery and self._check_stock_installed():

                if rec.sudo().mapped('picking_ids'):
                    if rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        rec.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                    rec._sh_unreseve_qty()

                    if rec._check_stock_account_installed():
                        # cancel related accouting entries
                        account_move = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                        account_move_line_ids = account_move.sudo().mapped('line_ids')
                        reconcile_ids = []
                        if account_move_line_ids:
                            reconcile_ids = account_move_line_ids.sudo().mapped('id')
                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                        account_move.sudo().write({'state':'draft','name':'/'})
                        account_move.sudo().with_context({'force_delete':True}).unlink()
                        
                        # cancel stock valuation
                        stock_valuation_layer_ids = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                        if stock_valuation_layer_ids:
                            stock_valuation_layer_ids.sudo().unlink()


                    rec.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            if rec.company_id.cancel_invoice:
                if rec.mapped('invoice_ids'):
                    if rec.mapped('invoice_ids'):
                        move = rec.mapped('invoice_ids')
                        move_line_ids = move.sudo().mapped('line_ids')

                        reconcile_ids = []
                        if move_line_ids:
                            reconcile_ids = move_line_ids.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        payments = False
                        if reconcile_lines:
                            payments = self.env['account.payment'].search(['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                                'credit_move_id').ids), ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])

                            reconcile_lines.sudo().unlink()

                            if payments:
                                if payments.sudo().mapped('move_id').mapped('line_ids'):
                                    payment_lines = payments.sudo().mapped('move_id').mapped('line_ids')
                                    reconcile_ids = payment_lines.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        move.mapped(
                            'line_ids.analytic_line_ids').sudo().unlink()

                        move_line_ids.sudo().write({'parent_state': 'draft'})
                        move.sudo().write({'state': 'draft'})

                        if payments:
                            payment_ids = payments
                            payment_ids.sudo().mapped(
                                'move_id').write({'state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped(
                                'line_ids').sudo().write({'parent_state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()
                            payment_ids.sudo().write({'state': 'cancel'})
#                             payment_ids.sudo().unlink()
                            payment_ids.sudo().mapped('move_id').with_context(
                                {'force_delete': True}).unlink()

                    rec.mapped('invoice_ids').sudo().write({'state': 'draft'})
            rec.sudo().write({'state': 'draft'})

    def action_sale_cancel_delete(self):
        for rec in self:
            if rec.company_id.cancel_delivery and self._check_stock_installed():

                if rec.sudo().mapped('picking_ids'):
                    if rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        rec.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                        rec._sh_unreseve_qty()

                        if rec._check_stock_account_installed():
                            # cancel related accouting entries
                            account_move = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                            account_move_line_ids = account_move.sudo().mapped('line_ids')
                            reconcile_ids = []
                            if account_move_line_ids:
                                reconcile_ids = account_move_line_ids.sudo().mapped('id')
                            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.sudo().unlink()
                            account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                            account_move.sudo().write({'state':'draft','name':'/'})
                            account_move.sudo().with_context({'force_delete':True}).unlink()
                            
                            # cancel stock valuation
                            stock_valuation_layer_ids = rec.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                            if stock_valuation_layer_ids:
                                stock_valuation_layer_ids.sudo().unlink()


                        rec.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().unlink()
                        rec.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').mapped('move_line_ids').sudo().unlink()

                    rec.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'draft'})
                    rec.sudo().mapped('picking_ids').sudo().unlink()

            if rec.company_id.cancel_invoice:

                if rec.mapped('invoice_ids'):
                    if rec.mapped('invoice_ids'):
                        move = rec.mapped('invoice_ids')
                        move_line_ids = move.sudo().mapped('line_ids')

                        reconcile_ids = []
                        if move_line_ids:
                            reconcile_ids = move_line_ids.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        payments = False
                        if reconcile_lines:

                            payments = self.env['account.payment'].search(['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                                'credit_move_id').ids), ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])
                            reconcile_lines.sudo().unlink()
                            if payments:
                                payment_ids = payments
                                if payment_ids.sudo().mapped('move_id').mapped('line_ids'):
                                    payment_lines = payment_ids.sudo().mapped('move_id').mapped('line_ids')
                                    reconcile_ids = payment_lines.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        move.mapped(
                            'line_ids.analytic_line_ids').sudo().unlink()

                        move_line_ids.sudo().write({'parent_state': 'draft'})
                        move.sudo().write({'state': 'draft'})

                        if payments:
                            payment_ids = payments
                            payment_ids.sudo().mapped(
                                'move_id').write({'state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped(
                                'line_ids').sudo().write({'parent_state': 'draft'})
                            payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                            payment_ids.sudo().write({'state': 'cancel'})
#                             payment_ids.sudo().unlink()
                            payment_ids.sudo().mapped('move_id').with_context(
                                {'force_delete': True}).unlink()

                    rec.mapped('invoice_ids').sudo().write({'state': 'draft'})
                    rec.mapped('invoice_ids').sudo().with_context(
                        {'force_delete': True}).unlink()

            rec.sudo().write({'state': 'cancel'})
            
        for rec in self:
            rec.sudo().unlink()
            
    def _sh_unreseve_qty(self):
        for move_line in self.sudo().mapped('picking_ids').mapped('move_ids_without_package').mapped('move_line_ids'):
            # unreserve qty
            quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity + move_line.qty_done})
            
            else:
                self.env['stock.quant'].sudo().create({'location_id': move_line.location_id.id,
                                                       'product_id': move_line.product_id.id,
                                                       'lot_id':move_line.lot_id.id,
                                                       'quantity':move_line.qty_done
                                                       })

            quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_dest_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity - move_line.qty_done})
            
            else:
                self.env['stock.quant'].sudo().create({'location_id': move_line.location_dest_id.id,
                                                       'product_id': move_line.product_id.id,
                                                       'lot_id':move_line.lot_id.id,
                                                       'quantity':move_line.qty_done * (-1)
                                                       })

    def sh_cancel(self):

        if self.company_id.cancel_delivery and self._check_stock_installed():
            if self.company_id.operation_type == 'cancel':
                if self.sudo().mapped('picking_ids'):
                    if self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        self.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'cancel'})
                        self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'cancel'})
                    self._sh_unreseve_qty()

                    if self._check_stock_account_installed():
                        # cancel related accouting entries
                        account_move = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                        account_move_line_ids = account_move.sudo().mapped('line_ids')
                        reconcile_ids = []
                        if account_move_line_ids:
                            reconcile_ids = account_move_line_ids.sudo().mapped('id')
                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                        account_move.sudo().write({'state':'draft','name':'/'})
                        account_move.sudo().with_context({'force_delete':True}).unlink()
                        
                        # cancel stock valuation
                        stock_valuation_layer_ids = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                        if stock_valuation_layer_ids:
                            stock_valuation_layer_ids.sudo().unlink()


                    self.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'cancel'})

            elif self.company_id.operation_type == 'cancel_draft':
                if self.sudo().mapped('picking_ids'):
                    if self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        self.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                    self._sh_unreseve_qty()

                    if self._check_stock_account_installed():
                        # cancel related accouting entries
                        account_move = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                        account_move_line_ids = account_move.sudo().mapped('line_ids')
                        reconcile_ids = []
                        if account_move_line_ids:
                            reconcile_ids = account_move_line_ids.sudo().mapped('id')
                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                        account_move.sudo().write({'state':'draft','name':'/'})
                        account_move.sudo().with_context({'force_delete':True}).unlink()
                        
                        # cancel stock valuation
                        stock_valuation_layer_ids = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                        if stock_valuation_layer_ids:
                            stock_valuation_layer_ids.sudo().unlink()

                    self.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            elif self.company_id.operation_type == 'cancel_delete':
                if self.sudo().mapped('picking_ids'):
                    if self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package'):
                        self.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().write({'state': 'draft'})
                        self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').mapped(
                            'move_line_ids').sudo().write({'state': 'draft'})
                        self._sh_unreseve_qty()

                        if self._check_stock_account_installed():
                            # cancel related accouting entries
                            account_move = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('account_move_ids')
                            account_move_line_ids = account_move.sudo().mapped('line_ids')
                            reconcile_ids = []
                            if account_move_line_ids:
                                reconcile_ids = account_move_line_ids.sudo().mapped('id')
                            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(['|',('credit_move_id','in',reconcile_ids),('debit_move_id','in',reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.sudo().unlink()
                            account_move.mapped('line_ids.analytic_line_ids').sudo().unlink()
                            account_move.sudo().write({'state':'draft','name':'/'})
                            account_move.sudo().with_context({'force_delete':True}).unlink()
                            
                            # cancel stock valuation
                            stock_valuation_layer_ids = self.sudo().mapped('picking_ids').sudo().mapped('move_ids_without_package').sudo().mapped('stock_valuation_layer_ids')
                            if stock_valuation_layer_ids:
                                stock_valuation_layer_ids.sudo().unlink()
                    


                        self.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').sudo().unlink()
                        self.sudo().mapped('picking_ids').sudo().mapped(
                            'move_ids_without_package').mapped('move_line_ids').sudo().unlink()

                    self.sudo().mapped('picking_ids').sudo().write(
                        {'state': 'draft'})
                    self.sudo().mapped('picking_ids').sudo().unlink()

        if self.company_id.cancel_invoice:

            if self.mapped('invoice_ids'):
                if self.mapped('invoice_ids'):
                    move = self.mapped('invoice_ids')
                    move_line_ids = move.sudo().mapped('line_ids')

                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.sudo().mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    payments = False
                    if reconcile_lines:
                        payments = self.env['account.payment'].search(['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                            'credit_move_id').ids), ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])
                        reconcile_lines.sudo().unlink()

                        if payments:
                            payment_ids = payments
                            if payment_ids.sudo().mapped('move_id').mapped('line_ids'):
                                payment_lines = payment_ids.sudo().mapped('move_id').mapped('line_ids')
                                reconcile_ids = payment_lines.sudo().mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.sudo().unlink()
                    move.mapped('line_ids.analytic_line_ids').sudo().unlink()

                    move_line_ids.sudo().write({'parent_state': 'draft'})
                    move.sudo().write({'state': 'draft'})

                    if payments:
                        payment_ids = payments
                        payment_ids.sudo().mapped(
                            'move_id').write({'state': 'draft'})
                        payment_ids.sudo().mapped('move_id').mapped(
                            'line_ids').sudo().write({'parent_state': 'draft'})
                        payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                        if self.company_id.operation_type == 'cancel':
                            payment_ids.sudo().write({'state': 'cancel'})
                        elif self.company_id.operation_type == 'cancel_draft':
                            payment_ids.sudo().write({'state': 'cancel'})
#                             payment_ids.sudo().unlink()
                        elif self.company_id.operation_type == 'cancel_delete':
                            payment_ids.sudo().write({'state': 'cancel'})
#                             payment_ids.sudo().unlink()

                        payment_ids.sudo().mapped('move_id').with_context(
                            {'force_delete': True}).unlink()

                if self.company_id.operation_type == 'cancel':
                    self.mapped('invoice_ids').sudo().write(
                        {'state': 'cancel'})
                elif self.company_id.operation_type == 'cancel_draft':
                    self.mapped('invoice_ids').sudo().write({'state': 'draft'})
                elif self.company_id.operation_type == 'cancel_delete':
                    self.mapped('invoice_ids').sudo().write(
                        {'state': 'draft', 'name': '/'})
                    self.mapped('invoice_ids').sudo().with_context(
                        {'force_delete': True}).unlink()

        if self.company_id.operation_type == 'cancel':
            self.sudo().write({'state': 'cancel'})
        elif self.company_id.operation_type == 'cancel_draft':
            self.sudo().write({'state': 'draft'})
        elif self.company_id.operation_type == 'cancel_delete':
            self.sudo().write({'state': 'cancel'})
            self.sudo().unlink()
            return {
                'name': 'Quotations',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
                'target': 'current',
                'context': {'search_default_my_quotation': 1}
            }
