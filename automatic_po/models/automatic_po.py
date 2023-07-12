from odoo import fields, models
import base64
import openpyxl
import io

import datetime


class dataUpload(models.TransientModel):
    _name = 'data.upload'

    data_file = fields.Binary(string='File', required=True)

    def import_data(self):

        decoded_data = base64.b64decode(self.data_file)
        xls_filelike = io.BytesIO(decoded_data)
        workbook = openpyxl.load_workbook(xls_filelike)
        sheet = workbook.active
        row = 1 + sheet.min_row
        mylist = []
        partner_obj = self.env["res.partner"]
        partner_name = sheet.cell(row, 1).value
        partner = partner_obj.search([('name', '=ilike', partner_name)], limit=1)
        nrows = sheet.max_row
        while row <= nrows + 1:
            if sheet.cell(row, 1).value != partner_name:
                values = {
                    'partner_id': partner.id,
                    'order_line': mylist
                }

                self.env['purchase.order'].create(values)
                if row == nrows + 1:
                    break
                partner_name = sheet.cell(row, 1).value
                partner = partner_obj.search([('name', '=ilike', partner_name)], limit=1)
                mylist = []

            product_template_id = self.env['product.template'].search(
                [('name', '=ilike', str(sheet.cell(row, 2).value))])
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id.id)])
            desc = product_template_id.name
            qty = str(sheet.cell(row, 3).value)
            rate = str(sheet.cell(row, 4).value)
            date = datetime.datetime.today()
            vals = (0, 0, {'product_id': product_id.id, 'name': desc, 'product_qty': qty, 'price_unit': rate,
                           'date_planned': date, 'product_uom': product_id.uom_id.id})

            if product_id:
                mylist.append(vals)
            else:
                print("Product not found on line # ", row)
            row += 1
