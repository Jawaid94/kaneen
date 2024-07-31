# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api
from odoo.exceptions import UserError


class TrelloLogger(models.Model):
    _name = 'sh.trello.log'
    _description = 'Helps you to maintain the activity done'
    _order = 'id desc'

    name = fields.Char("Name")
    error = fields.Char("Message")
    datetime = fields.Datetime("Date & Time")
    sh_trello_id = fields.Many2one('sh.trello.credentials')
    state = fields.Selection([('success', 'Success'), ('error', 'Failed')])
