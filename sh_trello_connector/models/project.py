# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models
import datetime
import re


class CreateTasks(models.Model):
    _inherit = 'project.task'
    card_id = fields.Char("Card ID")
    card_creation = fields.Datetime("Trello Creation Date")
    specific_export = fields.Boolean("Export To Trello")
    task_sync_specific = fields.Boolean("Last Sync", related="project_id.task_sync_specific")
    task_sync_all = fields.Boolean("Last sync all", related="project_id.task_sync_all")
    last_modified_date = fields.Datetime("Trello Modified Date")
    non_trello_tags = fields.Char('project.project')
    last_comment_done = fields.Datetime("Trello Last Comment Date", compute="_get_comment_date")

    def _get_comment_date(self):
        domain = [('res_id', '=', self.id)]
        find_comment = self.env['mail.message'].search(domain)
        self.last_comment_done = ''
        for comments in find_comment:
            message = re.sub('<[^<]+?>', '', comments.body)
            if message == 'Done' or message == 'done':
                self.last_comment_done = comments.date
            break


class CreateProject(models.Model):
    _inherit = 'project.project'

    board_id = fields.Char("Board ID")
    export_to_trello = fields.Boolean("Export To Trello")
    sh_creds_id = fields.Many2one("sh.trello.credentials", string="Trello Sync :")
    task_sync_all = fields.Boolean("All Tasks")
    task_sync_specific = fields.Boolean("Specific Tasks")
    project_ref = fields.One2many('project.specific', 'sh_project_id')


class CreateTags(models.Model):
    _inherit = 'project.tags'
    trello_id = fields.One2many('project.specific', 'sh_tag_id')


class ProjectSomething(models.Model):
    _name = 'project.specific'
    _description = 'strores Project Tags'
    sh_tag_id = fields.Many2one('project.tags')
    trello_tag = fields.Char(string="Trello Tag")
    sh_project_id = fields.Many2one('project.project')


class CreateStage(models.Model):
    _inherit = 'project.task.type'
    sstage_id = fields.Char("stage id")


class TrelloAttachment(models.Model):
    _inherit = "ir.attachment"
    trello_attachment_id = fields.Char("Attachment Id")


class MailMessage(models.Model):
    _inherit = 'mail.message'
    trello_comment_id = fields.Char("Trello Comment Id")
