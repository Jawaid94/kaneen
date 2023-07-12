import base64
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.base.models.res_bank import sanitize_account_number

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _parse_file(self, data_file):
        try:
            return self._parse_file_alrajhi(data_file)
        except Exception as e:
            return super(AccountBankStatementImport, self)._parse_file(data_file)

    def _parse_file_alrajhi(self, data_file):
        workbook = xlrd.open_workbook(file_contents=data_file or b'')

        sheet_obj = workbook.sheet_by_index(0)

        account_number = sheet_obj.cell(rowx=11, colx=2).value
        currency_code = 'SAR'

        row = 19
        max_row = sheet_obj.nrows
        vals_bank_statement = []
        transactions = []
        total_amt = 0.00
        for statement in range(row, max_row):
            str_dt = sheet_obj.cell(rowx=statement, colx=1).value
            if not str_dt:
                break
            dt = str(datetime.strptime(str_dt, "%d/%m/%Y").date())
            bank_account_id = partner_id = False

            remark = sheet_obj.cell(rowx=statement, colx=5).value
            if remark and not remark.isspace():
                remarks = remark.strip().split('/')
                if remarks:
                    for i in range(0, len(remarks)):
                        partner_bank = self.env['res.partner.bank'].search([('acc_number', '=', remarks[i].strip())], limit=1)
                        if partner_bank:
                            bank_account_id = partner_bank.id
                            partner_id = partner_bank.partner_id.id
                            break

            if sheet_obj.cell(rowx=statement, colx=6).value:
                # if credit -> make it with plus
                amount = float(sheet_obj.cell(rowx=statement, colx=6).value)
            else:
                # if debit -> make it with minus
                amount = -abs(float(sheet_obj.cell(rowx=statement, colx=7).value))

            vals_line = {
                'date': dt,
                'payment_ref': sheet_obj.cell(rowx=statement, colx=4).value,  # label
                'ref': remark.strip(),
                'amount': amount,
                'partner_bank_id': bank_account_id,
                'partner_id': partner_id,
                'transaction_type': sheet_obj.cell(rowx=statement, colx=9).value,
            }
            transactions.append(vals_line)

            total_amt += float(amount)

        vals_bank_statement.append({
            'transactions': transactions,
            # 'balance_start': float(account.statement.balance) - total_amt,
            'balance_end_real': total_amt,
        })

        return currency_code, account_number, vals_bank_statement