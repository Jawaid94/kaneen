# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class StockMoveUpdate(models.Model):
    _inherit = 'stock.move'

    move_date = fields.Date(string="Date")
    move_remark = fields.Char(string="Remarks")


class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    line_remark = fields.Char(string="Remark")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
