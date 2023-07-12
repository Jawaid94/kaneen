# -*- coding: utf-8 -*-

import io
import datetime
import itertools
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import models, fields
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class gen_journal_entry(models.TransientModel):
    _name = "gen.journal.entry"

    file_to_upload = fields.Binary('File')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

    def find_account_id(self, account_code):
        if account_code:
            account_ids = self.env['account.account'].search([('code', 'in', account_code.split('.'))])
            if account_ids:
                account_id = account_ids[0]
                return account_id
            else:
                raise ValidationError(_('"%s" Wrong Account Code') % (account_code))

    def check_desc(self, name):
        if name:
            return name
        else:
            return '/'

    def find_account_analytic_id(self, analytic_account_name):
        analytic_account_name = analytic_account_name.strip()
        analytic_account_id = self.env['account.analytic.account'].search([('name', 'ilike', analytic_account_name)])
        if analytic_account_id:
            analytic_account_id = analytic_account_id[0].id
            return analytic_account_id
        else:
            raise ValidationError(_('"%s" Wrong Analytic Account Name') % (analytic_account_name))

    def find_partner(self, partner_name):
        partner_name = partner_name.strip()
        partner_ids = self.env['res.partner'].search([('name', '=', partner_name), ('supplier_rank', '=', 1)])
        if partner_ids:
            partner_id = partner_ids[0]
            return partner_id
        else:
            partner_id = self.env['res.partner'].create(
                {'name': partner_name, 'supplier_rank': 1}
            )
            return partner_id

    def check_currency(self, cur_name):
        currency_ids = self.env['res.currency'].search([('name', '=', cur_name)])
        if currency_ids:
            currency_id = currency_ids[0]
            return currency_id
        else:
            currency_id = None
            return currency_id

    def create_import_move_lines(self, values):
        move_line_obj = self.env['account.move.line']
        move_obj = self.env['account.move']
        if values.get('partner'):
            partner_name = values.get('partner')
            if self.find_partner(partner_name) is not None:
                partner_id = self.find_partner(partner_name)
                values.update({'partner_id': partner_id.id})

        if values.get('currency'):
            cur_name = values.get('currency')
            if cur_name != '' and cur_name is not None:
                currency_id = self.check_currency(cur_name)
                if currency_id is not None:
                    values.update({'currency_id': currency_id.id})
                else:
                    raise ValidationError(_('"%s" Currency is not  in the system') % (cur_name))

        if values.get('name'):
            desc_name = values.get('name')
            name = self.check_desc(desc_name)
            values.update({'name': name})

        if values.get('date_maturity'):
            date = self.find_date(values.get('date_maturity'))
            values.update({'date_maturity': date})

        if values.get('date'):
            date = self.find_date(values.get('date'))
            values.update({'date': date})

        if values.get('account_code'):
            account_code = values.get('account_code')
            account_id = self.find_account_id(str(account_code))
            if account_id is not None:
                values.update({'account_id': account_id.id})
            else:
                raise ValidationError(_('"%s" Wrong Account Code') % (account_code))

        if values.get('debit') != '':
            values.update({'debit': float(values.get('debit'))})
            if float(values.get('debit')) > 0:
                values.update({'amount_currency': float(values.get('debit'))})
            if float(values.get('debit')) < 0:
                values.update({'credit': abs(values.get('debit'))})
                values.update({'debit': 0.0})
        else:
            values.update({'debit': float('0.0')})

        if values.get('name') == '':
            values.update({'name': '/'})

        if values.get('credit') != '':
            values.update({'credit': float(values.get('credit'))})
            if float(values.get('credit')) > 0:
                values.update({'amount_currency': -1 * float(values.get('credit'))})
            if float(values.get('credit')) < 0:
                values.update({'debit': abs(values.get('credit'))})
                values.update({'credit': 0.0})
        else:
            values.update({'credit': float('0.0')})

        if values.get('amount_currency') != '':
            values.update({'amount_currency': float(values.get('amount_currency'))})

        if values.get('analytic_account_id') != '':
            account_anlytic_account = values.get('analytic_account_id')
            if account_anlytic_account != '' or account_anlytic_account is None:
                analytic_account_id = self.find_account_analytic_id(account_anlytic_account)
                values.update({'analytic_account_id': analytic_account_id})
            else:
                raise ValidationError(_('"%s" Wrong Account Code') % (account_anlytic_account))

        if values.get('analytic_tag_ids') is not None:
            tags_list = []
            for x in values.get('analytic_tag_ids').split(','):
                x = x.strip()
                if x != '':
                    search_tag = self.env['account.analytic.tag'].search([('name', 'ilike', x)], limit=1)
                    if search_tag:
                        tags_list.append(search_tag.id)
            else:
                values.update({'analytic_tag_ids': [(6, 0, tags_list)]})

        return values

    def find_date(self, date):
        DATETIME_FORMAT = "%m/%d/%Y"
        if date:
            new_date = date.split(' ')
            try:
                p_date = datetime.strptime(new_date[0], DATETIME_FORMAT)
                return p_date
            except Exception:
                raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
        else:
            raise ValidationError(_('Please add Date field in sheet.'))

    def import_move_lines(self):
        keys = ['date', 'ref', 'journal', 'name', 'partner', 'analytic_account_id', 'analytic_tag_ids', 'account_code',
                'date_maturity', 'debit', 'credit', 'amount_currency', 'currency']
        try:
            csv_data = base64.b64decode(self.file_to_upload)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)
        except Exception:
            raise ValidationError(_("Invalid file!"))

        data = []
        for i in range(len(file_reader)):
            field = list(map(str, file_reader[i]))
            values = dict(zip(keys, field))
            if values:
                if i == 0:
                    continue
                else:
                    data.append(values)

        data1 = {}
        sorted_data = sorted(data, key=lambda x: x['ref'])
        for key, group in itertools.groupby(sorted_data, key=lambda x: x['ref']):
            small_list = []
            for i in group:
                small_list.append(i)
                data1.update({key: small_list})

        for key in data1.keys():
            lines = []
            values = data1.get(key)
            for val in values:
                res = self.create_import_move_lines(val)
                if not val.get('date') or not val.get('date_maturity'):
                    raise ValidationError(_('Define Date or Amount In Corresponding Columns !!!'))
                move_obj = self.env['account.move']
                if val.get('journal'):
                    journal_search = self.env['account.journal'].sudo().search(
                        [('name', '=', val.get('journal')), ('company_id', '=', self.company_id.id)])
                    if journal_search:
                        move1 = move_obj.search([('date', '=', val.get('date')), ('ref', '=', val.get('ref')),
                                                 ('journal_id', '=', journal_search.name)])
                        if move1:
                            move = move1
                        else:
                            move = move_obj.create({'date': val.get('date') or False, 'ref': val.get('ref') or False,
                                                    'journal_id': journal_search.id})
                    else:
                        raise ValidationError(_('Please Define Journal which are already in system.'))
                else:
                    raise ValidationError(_('Please Define Journal In Corresponding Columns !!!.'))
                del res['journal'], res['partner'], res['account_code'], res['currency']
                lines.append((0, 0, res))
            move.write({'line_ids': lines})


class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'

    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
