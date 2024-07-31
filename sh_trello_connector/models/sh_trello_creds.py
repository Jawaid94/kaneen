# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, _
import requests
from datetime import datetime
import base64
import json
from odoo.exceptions import UserError
import re
from os.path import join as opj
import pytz


class TrelloCreds(models.Model):
    _name = 'sh.trello.credentials'
    _description = 'Stores Your Trello Creds'

    name = fields.Char("Name")
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    last_sync = fields.Datetime("Last Sync Import")
    last_sync_export = fields.Datetime("Last Sync Export")
    api_key = fields.Char("Api Key")
    token = fields.Char("Token")
    auto_import = fields.Boolean("Auto Import")
    auto_export = fields.Boolean("Auto Export")
    trello_history = fields.One2many('sh.trello.log', 'sh_trello_id', string="Log History")
    refresh_import = fields.Boolean('Import on Refresh')
    refresh_export = fields.Boolean('Export on Refresh')
    no_of_task = fields.Integer("Import Limit", default="30")
    no_of_task_export = fields.Integer("Export Limit", default="20")
    unique = fields.Integer("Unique")
    length_card = fields.Integer("Length Card")
    length_card_export = fields.Integer("Length Card Export")
    final_count = fields.Integer()
    final_count_export = fields.Integer("Some Count")
    first_time = fields.Boolean("First Time")
    first_time_export = fields.Boolean("First Time Export")
    first_time_import = fields.Boolean("First Time Import")

    def submit(self):
        if self.api_key and self.token:
            query = {
                'key': self.api_key,
                'token': self.token
            }
            headers = {
                "Accept": "application/json"
            }
            get_boards_url = "https://api.trello.com/1/members/me/boards?fields=closed,name"
            list_board_id = []
            try:
                response = requests.get(url=get_boards_url, headers=headers, params=query)
                res_json = response.json()
            except:
                raise UserError(_("Please Enter Proper Credentials"))
            # Getting Board Name and creating Project
            for ids in res_json:
                status = ids['closed']
                if not status:
                    list_board_id.append(ids['id'])
                    board_id = ids['id']
                    project_name = ids['name']
                    domain = [('board_id', '=', board_id)]
                    already_created = self.env['project.project'].search(domain, limit=1)
                    if already_created:
                        vals_v = {
                            'name': project_name
                        }
                        already_created.write(vals_v)
                    else:
                        vals = {
                            'board_id': board_id,
                            'name': project_name,
                            'sh_creds_id': self.id,
                            'export_to_trello': True,
                            'task_sync_specific': True
                        }
                        self.env['project.project'].create(vals)

        # Getting Cards for each Board i.e Project
        if self.first_time:
            if not self.last_sync:
                self.last_sync = datetime.strptime('2002-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
            passing_list = []
            for data in list_board_id:
                get_board_url = "https://api.trello.com/1/boards/%s/cards?fields=dateLastActivity&since=2020-01-01" % data
                response = requests.get(url=get_board_url, headers=headers, params=query)
                res_json = response.json()
                for data in res_json:
                    last_modified_card = data['dateLastActivity']
                    start_date_last_sync = last_modified_card.split('T')[0]
                    start_time_last_sync = last_modified_card.split('T')[1].split('.')[0]
                    last_syncs = start_date_last_sync + " " + start_time_last_sync
                    last_modified_card = datetime.strptime(last_syncs, '%Y-%m-%d %H:%M:%S')
                    if self.last_sync < last_modified_card:
                        passing_list.append(data['id'])
            self.length_card = len(passing_list)
            count = []
            for i in range(self.length_card, 0, -1):
                count.append(i)
            dict_cardss = dict(zip(count, passing_list))
            if dict_cardss:
                message = self.card_turn(dict_cardss)
                return message
            else:
                vals = {
                    "name": self.name,
                    "sh_trello_id": self.id,
                    "state": "success",
                    "error": "Nothing Imported",
                    "datetime": datetime.now()
                }
                self.env['sh.trello.log'].create(vals)
                raise UserError(_("No Boards/Project To Import"))
        else:
            list_cards_id = []
            for data in list_board_id:
                get_board_url = "https://api.trello.com/1/boards/%s/cards" % data
                response = requests.get(url=get_board_url, headers=headers, params=query)
                res_json = response.json()
                for data in res_json:
                    list_cards_id.append(data['id'])
            self.length_card = len(list_cards_id)
            count = []
            for i in range(self.length_card, 0, -1):
                count.append(i)
            dict_cardss = dict(zip(count, list_cards_id))
            if dict_cardss:
                if self.first_time_import == False:
                    message = self.card_turn(dict_cardss)
                    return message
                else:
                    if self.no_of_task != 0 and self.length_card > self.no_of_task:
                        till = self.length_card - (self.final_count + self.no_of_task)
                        for i in range(self.length_card, till, -1):
                            del dict_cardss[i]
                        self.final_count = self.final_count + self.no_of_task
                        message = self.card_turn(dict_cardss)
                        return message
                    else:
                        message = self.card_turn(dict_cardss)
                        return message
            else:
                vals = {
                    "name": self.name,
                    "sh_trello_id": self.id,
                    "state": "success",
                    "error": "Nothing Imported",
                    "datetime": datetime.now()
                }
                self.env['sh.trello.log'].create(vals)
                raise UserError(_("No Boards/Project To Import"))

    def card_turn(self, dict_cardss):
        try:
            headers = {
                "Accept": "application/json"
            }
            query = {
                'key': self.api_key,
                'token': self.token
            }
            check_count = 0
            for count, card_ids in dict_cardss.items():
                check_count = check_count + 1
                # # Card Details
                card_details_url = "https://api.trello.com/1/cards/%s" % card_ids
                response = requests.get(url=card_details_url, headers=headers, params=query, timeout=60)
                res_json_cards = response.json()
                card_id = res_json_cards['id']
                last_modified_date = res_json_cards['dateLastActivity']
                start_date_last_sync = last_modified_date.split('T')[0]
                start_time_last_sync = last_modified_date.split('T')[1].split('.')[0]
                last_syncs = start_date_last_sync + " " + start_time_last_sync
                last_modified = datetime.strptime(last_syncs, '%Y-%m-%d %H:%M:%S')

                card_board_id = res_json_cards['idBoard']
                desc = res_json_cards['desc']
                name = res_json_cards['name']
                badges = res_json_cards['badges']
                comment = badges['comments']
                sequence_card = res_json_cards['pos']
                # Card Creation Date
                creation_time = datetime.fromtimestamp(int(card_id[0:8], 16))
                # Card Attachment
                card_attachment_url = "https://api.trello.com/1/cards/%s/attachments" % card_ids
                attch_response = requests.get(url=card_attachment_url, headers=headers, params=query)
                res_json_attach = attch_response.json()
                list_url = []
                filename = []
                attach_id_list = []
                for x in res_json_attach:
                    attach_id_list.append(x['id'])
                    filename.append(x['fileName'])
                    list_url.append(x['url'])
                dictionary = dict(zip(list_url, attach_id_list))
                # Card Labels
                tag_list = []
                name_list = []
                if res_json_cards['labels']:
                    color_dict = {
                        '1': 'red',
                        '2': 'orange',
                        '3': 'yellow',
                        '4': 'sky',
                        '5': 'black',
                        '6': 'pink',
                        '7': 'lime',
                        '8': 'blue',
                        '10': 'green',
                        '11': 'purple'
                    }
                    for ree in res_json_cards['labels']:
                        if ree['name']:
                            name_list.append(ree['name'])
                            domain = [('name', '=', ree['name'])]
                            already_present = self.env['project.tags'].search(domain, limit=1)
                            if already_present:
                                tag_list.append(already_present.id)
                            else:
                                tags_vals = {}
                                if ree['name'] != '':
                                    tags_vals['name'] = ree['name']
                                else:
                                    tags_vals['name'] = ree['color']
                                for intt, color in color_dict.items():
                                    if color == ree['color']:
                                        tags_vals['color'] = intt
                                create_tags = self.env['project.tags'].create(tags_vals)
                                tag_list.append(create_tags.id)
                                domain = [('board_id', '=', card_board_id)]
                                finds_proj = self.env['project.project'].search(domain, limit=1)
                                if finds_proj:
                                    specific_vals = {
                                        'trello_tag': ree['id'],
                                        'sh_tag_id': create_tags.id,
                                        'sh_project_id': finds_proj.id
                                    }
                                specific = self.env['project.specific'].create(specific_vals)
                                update_vals = {
                                    'trello_id': specific
                                }
                                create_tags.write(update_vals)
                            continue
                        domain = [('name', '=', ree['color'])]
                        already_present = self.env['project.tags'].search(domain, limit=1)
                        if already_present:
                            tag_list.append(already_present.id)
                        else:
                            # print("al",already_present.trello_id.sh_project_id)
                            tags_vals = {}
                            if ree['name'] != '':
                                tags_vals['name'] = ree['name']
                            else:
                                tags_vals['name'] = ree['color']
                            for intt, color in color_dict.items():
                                if color == ree['color']:
                                    tags_vals['color'] = intt
                            create_tags = self.env['project.tags'].create(tags_vals)
                            tag_list.append(create_tags.id)
                            domain = [('board_id', '=', card_board_id)]
                            finds_proj = self.env['project.project'].search(domain, limit=1)
                            if finds_proj:
                                specific_vals = {
                                    'trello_tag': ree['id'],
                                    'sh_tag_id': create_tags.id,
                                    'sh_project_id': finds_proj.id
                                }
                            specific = self.env['project.specific'].create(specific_vals)
                            update_vals = {
                                'trello_id': specific
                            }
                            create_tags.write(update_vals)
                # # Card Stage
                list_url = "https://trello.com/1/cards/%s/list" % card_ids
                response_list = requests.get(url=list_url, params=query)
                res_json_list = response_list.json()
                stage_name = res_json_list['name']
                position = res_json_list['pos']
                stage_id = res_json_list['id']
                domain = [('board_id', '=', card_board_id)]
                find_project = self.env['project.project'].search(domain)
                domain = [('card_id', '=', card_id)]
                find_task = self.env['project.task'].search(domain, limit=1)
                # Calling write method if already_created for Tasks
                if find_task:
                    for project in find_project:
                        domain = [('name', '=', stage_name)]
                        find_stage = self.env['project.task.type'].search(domain, limit=1)
                        if find_stage:
                            vals = {
                                'project_id': project.id,
                                'card_id': card_ids,
                                'stage_id': find_stage.id,
                                'tag_ids': tag_list,
                                'description': desc if desc else '',
                                'name': name,
                                'last_modified_date': last_modified,
                                'card_creation': creation_time,
                                'sequence': sequence_card,
                                'specific_export': True
                            }
                            find_task.write(vals)
                            for url, idd in dictionary.items():
                                domain = [('trello_attachment_id', '=', idd)]
                                find_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if find_attachment:
                                    continue
                                else:
                                    ir_vals = {
                                        'name': "Attachment",
                                        'type': 'url',
                                        'url': url,
                                        'res_model': 'project.task',
                                        'res_name': find_task.name,
                                        'res_id': find_task.id,
                                        'trello_attachment_id': idd
                                    }
                                    self.env['ir.attachment'].create(ir_vals)
                        else:
                            vals_stage = {
                                'name': stage_name,
                                'project_ids': project.ids,
                                'sequence': position,
                                'sstage_id': stage_id
                            }
                            create_stage = self.env['project.task.type'].create(vals_stage)
                            vals = {
                                'project_id': project.id,
                                'card_id': card_ids,
                                'tag_ids': tag_list,
                                'stage_id': create_stage.id,
                                'description': desc if desc else '',
                                'name': name,
                                'last_modified_date': last_modified,
                                'card_creation': creation_time,
                                'sequence': sequence_card,
                                'specific_export': True,
                            }
                            find_task.write(vals)
                            for url, idd in dictionary.items():
                                domain = [('trello_attachment_id', '=', idd)]
                                find_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if find_attachment:
                                    continue
                                else:
                                    ir_vals = {
                                        'name': "Attachment",
                                        'type': 'url',
                                        'url': url,
                                        'res_model': 'project.task',
                                        'res_name': find_task.name,
                                        'res_id': find_task.id,
                                        'trello_attachment_id': idd
                                    }

                                    self.env['ir.attachment'].create(ir_vals)
                # Creating Task if not created
                else:
                    for project in find_project:
                        domain = [('name', '=', stage_name)]
                        find_stage = self.env['project.task.type'].search(domain, limit=1)
                        if find_stage:
                            vals = {
                                'project_id': project.id,
                                'card_id': card_ids,
                                'tag_ids': tag_list,
                                'stage_id': find_stage.id,
                                'description': desc if desc else '',
                                'name': name,
                                'last_modified_date': last_modified,
                                'card_creation': creation_time,
                                'sequence': sequence_card,
                                'specific_export': True,
                            }
                            create_task = self.env['project.task'].create(vals)
                            for url, idd in dictionary.items():
                                domain = [('trello_attachment_id', '=', idd)]
                                find_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if find_attachment:
                                    continue
                                else:
                                    ir_vals = {
                                        'name': "Attachment",
                                        'type': 'url',
                                        'url': url,
                                        'res_model': 'project.task',
                                        'res_name': create_task.name,
                                        'res_id': create_task.id,
                                        'trello_attachment_id': idd
                                    }
                                    self.env['ir.attachment'].create(ir_vals)
                        else:
                            vals_stage = {
                                'name': stage_name,
                                'project_ids': project.ids,
                                'sequence': position,
                                'sstage_id': stage_id
                            }
                            create_stage = self.env['project.task.type'].create(vals_stage)
                            vals = {
                                'project_id': project.id,
                                'card_id': card_id,
                                'tag_ids': tag_list,
                                'stage_id': create_stage.id,
                                'description': desc if desc else '',
                                'name': name,
                                'last_modified_date': last_modified,
                                'card_creation': creation_time,
                                'sequence': sequence_card,
                                'sequence': sequence_card,
                                'specific_export': True,
                            }
                            create_task = self.env['project.task'].create(vals)
                            for url, idd in dictionary.items():
                                domain = [('trello_attachment_id', '=', idd)]
                                find_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if find_attachment:
                                    continue
                                else:
                                    ir_vals = {
                                        'name': "Attachment",
                                        'type': 'url',
                                        'url': url,
                                        'res_model': 'project.task',
                                        'res_name': create_task.name,
                                        'res_id': create_task.id,
                                        'trello_attachment_id': idd
                                    }
                                    self.env['ir.attachment'].create(ir_vals)
                if comment != 0:
                    card_comment_url = "https://api.trello.com/1/cards/%s/actions?filter=commentCard" % card_ids
                    comment_response = requests.get(url=card_comment_url, headers=headers, params=query)
                    comment_data_json = comment_response.json()
                    for x in comment_data_json[::-1]:
                        vals_11 = {}
                        text = x['data']['text']
                        lst = text.split(']')
                        comment_id = x['id']
                        card_id = x['data']['card']['id']
                        user = x['memberCreator']['username']
                        comment_date = x['date']
                        start_date_last_sync = comment_date.split('T')[0]
                        start_time_last_sync = comment_date.split('T')[1].split('.')[0]
                        last_syncs = start_date_last_sync + " " + start_time_last_sync
                        comment_dates = datetime.strptime(last_syncs, '%Y-%m-%d %H:%M:%S')
                        domain = [('email', '=', user)]
                        dates = x['date']
                        find_user = self.env['res.partner'].search(domain, limit=1)
                        domain = [('card_id', '=', card_id)]
                        find_task_id = self.env['project.task'].search(domain, limit=1)
                        domain = [('trello_comment_id', '=', comment_id)]
                        find_comment = self.env['mail.message'].search(domain, limit=1)
                        if find_comment:
                            continue
                        elif find_user and find_task_id:
                            vals_11 = {
                                'model': 'project.task',
                                'message_type': 'comment',
                                'res_id': find_task_id.id,
                                'author_id': find_user.id,
                                'date': comment_dates,
                                'trello_comment_id': comment_id
                            }
                            if "http://" in text or "https://" in text:
                                lst = text.split(']')
                                if "http://" in lst[0] or "https://" in lst[0]:
                                    uurl = lst[0][1:-1]
                                elif lst[1]:
                                    uurl = lst[1][1:-1]
                                domain = [('url', '=', uurl)]
                                attach_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if attach_attachment.id > 1:
                                    vals_11['attachment_ids'] = attach_attachment.ids
                                elif "http://" in lst[0] or "https://" in lst[0]:
                                    uurl = lst[0][1:-2]
                                else:
                                    uurl = lst[1][1:-2]
                                domain = [('url', '=', uurl)]
                                attach_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                vals_11['attachment_ids'] = attach_attachment.ids
                                vals_11['body'] = lst[0]
                            else:
                                vals_11['body'] = text
                            self.env['mail.message'].create(vals_11)
                        else:
                            vals = {
                                'name': user,
                                'email': user
                            }
                            create_instant_user = self.env['res.partner'].create(vals)
                            vals_22 = {
                                'model': 'project.task',
                                'message_type': 'comment',
                                'res_id': find_task_id.id,
                                'author_id': create_instant_user.id,
                                'date': comment_dates,
                                'trello_comment_id': comment_id
                            }
                            if "http://" in text or "https://" in text:
                                lst = text.split(']')
                                if "http://" in lst[0] or "https://" in lst[0]:
                                    uurl = lst[0][1:-1]
                                elif lst[1]:
                                    uurl = lst[1][1:-1]
                                domain = [('url', '=', uurl)]
                                attach_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                if attach_attachment.id > 1:
                                    vals_11['attachment_ids'] = attach_attachment.ids
                                elif "http://" in lst[0] or "https://" in lst[0]:
                                    uurl = lst[0][1:-2]
                                else:
                                    uurl = lst[1][1:-2]
                                domain = [('url', '=', uurl)]
                                attach_attachment = self.env['ir.attachment'].search(domain, limit=1)
                                vals_22['attachment_ids'] = attach_attachment.ids
                                vals_22['body'] = lst[0]
                            else:
                                vals_22['body'] = text
                            create_chat = self.env['mail.message'].create(vals_22)
                if count == 1:
                    self.unique = 0
                    self.first_time = True
                    self.first_time_import = True
                    self.final_count = 0
                    self.last_sync = datetime.now()
                    vals = {
                        "name": self.name,
                        "sh_trello_id": self.id,
                        "state": "success",
                        "error": "Impoted Successfully",
                        "datetime": datetime.now()
                    }
                    self.env['sh.trello.log'].create(vals)
                    return "Imported Succesfully"
                if check_count == self.no_of_task:
                    self.first_time_import = True
                    vals = {
                        "name": self.name,
                        "sh_trello_id": self.id,
                        "state": "success",
                        "error": "Partially Imported,Import Again (%s) left" % (count),
                        "datetime": datetime.now()
                    }
                    self.env['sh.trello.log'].create(vals)
                    return "Partially Imported,Refresh Again"
        except Exception as e:
            vals = {
                "name": self.name,
                "sh_trello_id": self.id,
                "state": "error",
                "error": e,
                "datetime": datetime.now()
            }
            self.env['sh.trello.log'].create(vals)
            return "Partially Imported,Refresh Again"

    def import_all(self):
        for data in self:
            data.submit()

    def export_all(self):
        for data in self:
            data.export_trello()

    def _trello_import_cron(self):
        domain = []
        find_object = self.env['sh.trello.credentials'].search(domain)
        for record in find_object:
            if record.auto_import:
                record.submit()
            if record.auto_export:
                record.export_trello()

    def trello_refresh(self, task_ids=None):
        if self.env.user.has_group('sh_trello_connector.sh_featch_latest_task'):
            if self:
                ids = self.env['project.project'].browse(self.id)
                domain = [('id', '=', ids.sh_creds_id.id)]
                trello_cred = self.env['sh.trello.credentials'].sudo().search(domain)
                if trello_cred.refresh_import or trello_cred.refresh_export:
                    if trello_cred.refresh_import:
                        catch = trello_cred.submit()
                        return catch
                    if trello_cred.refresh_export:
                        catch_export = trello_cred.export_trello()
                        return catch_export
                else:
                    return "Please select import of export from configuration"
            else:
                for xy in task_ids:
                    ids = self.env['project.task'].browse(xy)
                    domain = [('id', '=', ids.project_id.sh_creds_id.id)]
                    trello_cred = self.env['sh.trello.credentials'].sudo().search(domain)
                    if trello_cred.refresh_import or trello_cred.refresh_export:
                        if trello_cred.refresh_import:
                            catch = trello_cred.submit()
                            return catch
                        if trello_cred.refresh_export:
                            catch_export = trello_cred.export_trello()
                            return catch_export
                    else:
                        return "Please select import or export from configuration"
        else:
            return "Permission Not Granted"

    def export_trello(self):
        if not self.last_sync_export:
            self.last_sync_export = datetime.strptime('2002-01-04 00:00:00', '%Y-%m-%d %H:%M:%S')
        headers = {
            "Accept": "application/json"
        }
        query = {
            'key': self.api_key,
            'token': self.token
        }
        get_boards_url = "https://api.trello.com/1/members/me/boards?fields=closed,name"
        list_board_id = []
        try:
            response = requests.get(url=get_boards_url, headers=headers, params=query)
            res_json = response.json()
        except:
            raise UserError(_("Pelase Enter Proper Credentials"))
        for ids in res_json:
            status = ids['closed']
            if not status:
                if 'id' in res_json:
                    list_board_id.append(ids['id'])
        export_list = []
        domain = [('export_to_trello', '=', True)]
        export_project = self.env['project.project'].search(domain)
        if export_project:
            for values in export_project:
                # Creating and Updating Project
                if values.board_id:
                    if values.board_id in list_board_id:
                        update_project_url = "https://api.trello.com/1/boards/%s" % (values.board_id)
                        query = {
                            'key': values.sh_creds_id.api_key,
                            'token': values.sh_creds_id.token,
                            'name': values.name
                        }
                        response_update_url = requests.put(url=update_project_url, params=query)
                else:
                    query = {
                        'key': values.sh_creds_id.api_key,
                        'token': values.sh_creds_id.token,
                        'name': values.name,
                        'defaultLists': 'false'
                    }
                    try:
                        create_board_url = "https://api.trello.com/1/boards/"
                        create_response = requests.post(url=create_board_url, headers=headers, params=query)
                        create_json = create_response.json()
                        vals = {
                            'board_id': create_json['id']
                        }
                        values.write(vals)
                    except Exception as e:
                        raise UserError(_("Something went Wrong, try again later"))
                # Creating and updating stages
                if values.sh_stage_ids:
                    for name in values.sh_stage_ids[::-1]:
                        query_stage = {
                            'key': values.sh_creds_id.api_key,
                            'token': values.sh_creds_id.token,
                            'name': name.name,
                            'pos': name.sequence
                        }
                        if name.sstage_id:
                            domain = [('write_date', '>', self.last_sync_export)]
                            get_stages = name.search(domain)
                            if get_stages:
                                update_stage_url = "https://api.trello.com/1/lists/%s" % (name.sstage_id)
                                query_stage['idBoard'] = values.board_id
                                update_stage_response = requests.put(url=update_stage_url, params=query_stage)
                        else:
                            create_list_url = "https://api.trello.com/1/lists"
                            if values.board_id:
                                query_stage['idBoard'] = values.board_id
                            else:
                                query_stage['idBoard'] = create_json['id']
                            response_create_list = requests.post(url=create_list_url, headers=headers,
                                                                 params=query_stage)
                            create_list_json = response_create_list.json()
                            vals = {
                                'sstage_id': create_list_json['id']
                            }
                            name.write(vals)
                # Creating new Tasks
            domain = ['|', ('specific_export', '=', True), ('task_sync_all', '=', True)]
            get_tasks = self.env['project.task'].search(domain)
            for tasks in get_tasks:
                if tasks.project_id.board_id and tasks.project_id in list_board_id:
                    export_list.append(tasks)
                else:
                    export_list.append(tasks)
            self.length_card_export = len(export_list)
            count = []
            for i in range(self.length_card_export, 0, -1):
                count.append(i)
            export_cardss = dict(zip(count, export_list))
            if export_cardss:
                if not self.first_time_export:
                    message = self.partial_export(export_cardss)
                    return message
                else:
                    if self.no_of_task != 0 and self.length_card > self.no_of_task:
                        till = self.length_card_export - (self.final_count_export + self.no_of_task_export)
                        for i in range(self.length_card_export, till, -1):
                            del export_cardss[i]
                        self.final_count_export = self.final_count_export + self.no_of_task_export
                        message = self.partial_export(export_cardss)
                        return message
                    else:
                        message = self.partial_export(export_cardss)
                        return message
            else:
                vals = {
                    "name": self.name,
                    "sh_trello_id": self.id,
                    "state": "success",
                    "error": "Nothing Exported",
                    "datetime": datetime.now()
                }
                self.env['sh.trello.log'].create(vals)
                return "Nothing To Export"
        else:
            raise UserError(_("No Board/Project To Export"))

    def partial_export(self, export_list):
        check_count = 0
        for counts, task in export_list.items():
            check_count = check_count + 1
            headers = {
                "Accept": "application/json"
            }
            if task.task_sync_specific or task.task_sync_all:
                color_dict = {
                    '1': 'red',
                    '2': 'orange',
                    '3': 'yellow',
                    '4': 'sky',
                    '5': 'black',
                    '6': 'pink',
                    '7': 'lime',
                    '8': 'blue',
                    '10': 'green',
                    '11': 'purple'
                }
                color_name = ['red', 'green', 'orange', 'blue', 'yellow', 'purple', 'pink']
                # Creating new label
                trello_list = []
                non_trello_list = []
                final_list_id = []
                query_label = {
                    'key': task.project_id.sh_creds_id.api_key,
                    'token': task.project_id.sh_creds_id.token,
                    'idBoard': task.project_id.board_id
                }
                for x in task.tag_ids:
                    count = 1
                    domain = [('write_date', '>', self.last_sync_export)]
                    get_labels = x.search(domain)
                    for y in x.trello_id:
                        if get_labels:
                            update_label_url = "https://api.trello.com/1/labels/%s" % (y.trello_tag)
                            update_label_response = requests.put(url=update_label_url, params=query_label)
                        else:
                            if count > 1:
                                continue
                            if task.project_id.id == y.sh_project_id.id:
                                count = count + 1
                                trello_list.append(y.trello_tag)
                                non_trello_list.append(x.id)
                    if x.id not in non_trello_list:
                        final_list_id.append(x.id)
                tags = self.env['project.tags'].browse(final_list_id)
                for ree in tags:
                    create_label_url = "https://api.trello.com/1/labels"

                    if ree.name in color_name:
                        query_label['name'] = ''
                    else:
                        query_label['name'] = ree.name
                    for key, value in color_dict.items():
                        if int(key) == ree.color:
                            query_label['color'] = value
                    response_create_label = requests.post(url=create_label_url, headers=headers, params=query_label)
                    response_create_label_json = response_create_label.json()
                    new_vals = {
                        'sh_tag_id': ree.id,
                        'sh_project_id': task.project_id.id,
                        'trello_tag': response_create_label_json['id']
                    }
                    create_new_trello = self.env['project.specific'].create(new_vals)
                    trello_list.append(response_create_label_json['id'])
                domain = [('write_date', '>', self.last_sync_export)]
                get_tasks = task.search(domain)
                query_task = {
                    'key': self.api_key,
                    'token': self.token,
                    'name': task.name,
                    'pos': task.sequence,
                    'idBoard': task.project_id.board_id
                }
                if trello_list:
                    query_task['idLabels'] = trello_list
                if task.description:
                    description = re.sub('<[^<]+?>', '', task.description)
                    query_task['desc'] = description
                if task.date_deadline:
                    query_task['due'] = task.date_deadline
                if task.stage_id.sstage_id:
                    query_task['idList'] = task.stage_id.sstage_id
                if get_tasks and task.card_id:
                    update_task_url = "https://api.trello.com/1/cards/%s" % (task.card_id)
                    update_task_response = requests.put(url=update_task_url, headers=headers, params=query_task)
                else:
                    create_task_url = "https://api.trello.com/1/cards"
                    response_task = requests.post(url=create_task_url, headers=headers, params=query_task)
                    if response_task.status_code == 200:
                        response_task_json = response_task.json()
                        card_vals = {
                            'card_id': response_task_json['id']
                        }
                        task.write(card_vals)
                domain = [('res_id', '=', task.id)]
                get_attachment = self.env['ir.attachment'].search(domain)
                if get_attachment:
                    for attachment in get_attachment:
                        if attachment.trello_attachment_id:
                            continue
                        else:
                            url = ''
                            domain = [('key', '=', 'web.base.url')]
                            config = self.env['ir.config_parameter'].sudo().search(domain)
                            url = config.value + '/web/content/ir.attachment'

                            url = url + '/' + str(attachment.id) + '/datas?download=true'

                            if attachment.access_token:
                                url += '&access_token=' + attachment.access_token
                            else:
                                attachment.generate_access_token()
                                url += '&access_token=' + attachment.access_token

                            create_attachment_url = "https://api.trello.com/1/cards/%s/attachments" % (task.card_id)
                            headers = {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                            }
                            query_attachement = {
                                'key': task.project_id.sh_creds_id.api_key,
                                'token': task.project_id.sh_creds_id.token,
                                'name': attachment.name,
                                'url': url
                            }
                            create_attachment = requests.post(url=create_attachment_url, headers=headers,
                                                              params=query_attachement)
                            create_attachment_json = create_attachment.json()
                            if create_attachment_json:
                                vals = {
                                    'trello_attachment_id': create_attachment_json['id']
                                }
                                attachment.write(vals)
                domain = [('res_id', '=', task.id), ('write_date', '>', self.last_sync_export)]
                get_comments = self.env['mail.message'].search(domain)
                if get_comments:
                    for comment in get_comments[::-1]:
                        if comment.trello_comment_id:
                            continue
                        elif comment.body:
                            comment_url = "https://api.trello.com/1/cards/%s/actions/comments" % (task.card_id)
                            message = re.sub('<[^<]+?>', '', comment.body)
                            comment_query = {
                                'key': task.project_id.sh_creds_id.api_key,
                                'token': task.project_id.sh_creds_id.token,
                                'text': message
                            }
                            if comment.attachment_ids:
                                comment_query['text'] = ''
                                url_list = []
                                for attachment in comment.attachment_ids:
                                    url = ''
                                    domain = [('key', '=', 'web.base.url')]
                                    config = self.env['ir.config_parameter'].sudo().search(domain)
                                    url = config.value + '/web/content/ir.attachment'

                                    url = url + '/' + str(attachment.id) + '/datas?download=true'

                                    if attachment.access_token:
                                        url += '&access_token=' + attachment.access_token
                                    else:
                                        attachment.generate_access_token()
                                        url += '&access_token=' + attachment.access_token
                                    url_list.append(url)
                                urls = '  '.join(url_list)
                                comment_query['text'] = message + ' ' + urls
                            com_response = requests.post(url=comment_url, params=comment_query)
                            create_comment_json = com_response.json()
                            if create_comment_json:
                                vals = {
                                    'trello_comment_id': create_comment_json['id']
                                }
                                comment.write(vals)
            if check_count == self.no_of_task_export:
                self.first_time_export = True
                vals = {
                    "name": self.name,
                    "sh_trello_id": self.id,
                    "state": "success",
                    "error": "Partially Exported,Export Again ",
                    "datetime": datetime.now()
                }
                self.env['sh.trello.log'].create(vals)
                return "Partially Exported,Refresh Again"
            if counts == 1:
                self.last_sync_export = datetime.now()
                self.final_count_export = 0
                self.first_time_export == False
                vals = {
                    "name": self.name,
                    "sh_trello_id": self.id,
                    "state": "success",
                    "error": "Exported Successfully",
                    "datetime": datetime.now()
                }
                self.env['sh.trello.log'].create(vals)
                return "Exported Successfully"
