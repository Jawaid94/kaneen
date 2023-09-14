# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models


class Payment(models.Model):
    _inherit = 'account.payment'

    def action_payment_cancel(self):
        for rec in self:
            if rec.sudo().mapped('move_id').mapped('line_ids'):
                payment_lines = rec.sudo().mapped('move_id').mapped('line_ids')
                reconcile_ids = payment_lines.sudo().mapped('id')

                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()
            rec.sudo().mapped('move_id').write({'state': 'draft', 'name': '/'})

            rec.sudo().mapped('move_id').mapped(
                'line_ids').sudo().write({'parent_state': 'draft'})
            rec.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()
            #             rec.sudo().mapped('move_id').with_context({'force_delete':True}).unlink()
            rec.sudo().write({'state': 'cancel'})

    def action_payment_cancel_draft(self):
        for rec in self:
            if rec.sudo().mapped('move_id').mapped('line_ids'):
                payment_lines = rec.sudo().mapped('move_id').mapped('line_ids')
                reconcile_ids = payment_lines.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()

            rec.sudo().mapped('move_id').write({'state': 'draft', 'name': '/'})
            rec.sudo().mapped('move_id').mapped(
                'line_ids').sudo().write({'parent_state': 'draft'})
            #             rec.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()
            #             rec.sudo().mapped('move_id').with_context({'force_delete':True}).unlink()
            rec.sudo().write({'state': 'draft'})

    def action_payment_cancel_delete(self):
        for rec in self:

            if rec.sudo().mapped('move_id').mapped('line_ids'):
                payment_lines = rec.sudo().mapped('move_id').mapped('line_ids')
                reconcile_ids = payment_lines.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.sudo().unlink()

            rec.sudo().mapped('move_id').write({'state': 'draft', 'name': '/'})
            rec.sudo().mapped('move_id').mapped(
                'line_ids').sudo().write({'parent_state': 'draft'})
            rec.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()
            #             rec.sudo().mapped('move_id').with_context({'force_delete':True}).unlink()
            rec.sudo().write({'state': 'draft'})
            rec.sudo().unlink()

    def sh_cancel(self):

        if self.sudo().mapped('move_id').mapped('line_ids'):
            payment_lines = self.sudo().mapped('move_id').mapped('line_ids')
            reconcile_ids = payment_lines.sudo().mapped('id')

            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.sudo().unlink()

        self.sudo().mapped('move_id').write({'state': 'draft', 'name': '/'})
        self.sudo().mapped('move_id').mapped(
            'line_ids').sudo().write({'parent_state': 'draft'})
        #         self.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

        #         self.sudo().mapped('move_id').with_context({'force_delete':True}).unlink()

        if self.company_id.payment_operation_type == 'cancel':
            self.sudo().write({'state': 'cancel'})
        elif self.company_id.payment_operation_type == 'cancel_draft':
            self.sudo().write({'state': 'draft'})
        elif self.company_id.payment_operation_type == 'cancel_delete':
            self.sudo().write({'state': 'draft'})
            self.sudo().unlink()
            return {
                'name': 'Payments',
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form,graph',
                'target': 'current',
            }


class Invoice(models.Model):
    _inherit = 'account.move'

    def action_invoice_cancel(self):
        for rec in self:

            move = rec
            move_line_ids = move.sudo().mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.sudo().mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            payments = False
            if reconcile_lines:
                payments = self.env['account.payment'].search(
                    ['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                        'credit_move_id').ids),
                     ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])

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

            if payments:
                payment_ids = payments
                payment_ids.sudo().mapped('move_id').write(
                    {'state': 'draft', 'name': '/'})

                payment_ids.sudo().mapped('move_id').mapped(
                    'line_ids').sudo().write({'parent_state': 'draft'})
                payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                if rec.company_id.payment_operation_type == 'cancel':
                    payment_ids.sudo().write({'state': 'cancel'})
                elif rec.company_id.payment_operation_type == 'cancel_draft':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                elif rec.company_id.payment_operation_type == 'cancel_delete':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                    payment_ids.sudo().unlink()

                payment_ids.sudo().mapped('move_id').with_context(
                    {'force_delete': True}).unlink()

            move_line_ids.sudo().write({'parent_state': 'draft'})
            move.sudo().write({'state': 'draft', 'name': '/'})

            rec.sudo().write({'state': 'cancel'})

    def action_invoice_cancel_draft(self):
        for rec in self:

            move = rec
            move_line_ids = move.sudo().mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.sudo().mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            payments = False
            if reconcile_lines:
                payments = self.env['account.payment'].search(
                    ['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                        'credit_move_id').ids),
                     ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])

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

            if payments:
                payment_ids = payments
                payment_ids.sudo().mapped('move_id').write(
                    {'state': 'draft', 'name': '/'})
                payment_ids.sudo().mapped('move_id').mapped(
                    'line_ids').sudo().write({'parent_state': 'draft'})
                payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                if rec.company_id.payment_operation_type == 'cancel':
                    payment_ids.sudo().write({'state': 'cancel'})
                elif rec.company_id.payment_operation_type == 'cancel_draft':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                elif rec.company_id.payment_operation_type == 'cancel_delete':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                    payment_ids.sudo().unlink()

                payment_ids.sudo().mapped('move_id').with_context(
                    {'force_delete': True}).unlink()

            move_line_ids.sudo().write({'parent_state': 'draft', 'name': '/'})
            move.sudo().write({'state': 'draft'})

            rec.sudo().write({'state': 'draft', 'name': '/'})

    def action_invoice_cancel_delete(self):
        for rec in self:

            move = rec
            move_line_ids = move.sudo().mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.sudo().mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            payments = False
            if reconcile_lines:
                payments = self.env['account.payment'].search(
                    ['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                        'credit_move_id').ids),
                     ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])
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

            if payments:
                payment_ids = payments
                payment_ids.sudo().mapped('move_id').write(
                    {'state': 'draft', 'name': '/'})
                payment_ids.sudo().mapped('move_id').mapped(
                    'line_ids').sudo().write({'parent_state': 'draft'})
                payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

                if rec.company_id.payment_operation_type == 'cancel':
                    payment_ids.sudo().write({'state': 'cancel'})
                elif rec.company_id.payment_operation_type == 'cancel_draft':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                elif rec.company_id.payment_operation_type == 'cancel_delete':
                    payment_ids.sudo().write(
                        {'state': 'draft', 'move_name': ''})
                    payment_ids.sudo().unlink()

                payment_ids.sudo().mapped('move_id').with_context(
                    {'force_delete': True}).unlink()

            move_line_ids.sudo().write({'parent_state': 'draft'})
            move.sudo().write({'state': 'draft'})

            rec.sudo().write({'state': 'draft', 'name': '/'})
            rec.sudo().with_context({'force_delete': True}).unlink()

    def sh_cancel(self):

        move = self
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

        if payments:
            payment_ids = payments
            payment_ids.sudo().mapped('move_id').write(
                {'state': 'draft', 'name': '/'})

            payment_ids.sudo().mapped('move_id').mapped(
                'line_ids').sudo().write({'parent_state': 'draft'})
            payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()

            if self.company_id.payment_operation_type == 'cancel':
                payment_ids.sudo().write({'state': 'cancel'})
            elif self.company_id.payment_operation_type == 'cancel_draft':
                payment_ids.sudo().write({'state': 'cancel'})
            elif self.company_id.payment_operation_type == 'cancel_delete':
                payment_ids.sudo().write({'state': 'cancel'})
            #                 payment_ids.sudo().unlink()

            payment_ids.sudo().mapped('move_id').with_context(
                {'force_delete': True}).unlink()

        move_line_ids.sudo().write({'parent_state': 'draft'})
        move.sudo().write({'state': 'draft'})

        if self.company_id.invoice_operation_type == 'cancel':
            self.sudo().write({'state': 'cancel'})
        elif self.company_id.invoice_operation_type == 'cancel_draft':
            self.sudo().write({'state': 'draft', 'name': '/'})
        elif self.company_id.invoice_operation_type == 'cancel_delete':
            self.sudo().write({'state': 'draft', 'name': '/'})

        if self.company_id.invoice_operation_type == 'cancel_delete':
            self.sudo().with_context({'force_delete': True}).unlink()
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form',
                'target': 'current',
            }
