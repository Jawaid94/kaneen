from odoo import models


class CategoryXlsx(models.AbstractModel):
    _name = 'report.kn_customization.report_category_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # def action_done(self):
    #     mail_template = self.env.ref("mail.email_template_form")
    #     mail_template_send_mail(self.id, force_send=True)

    def generate_xlsx_report(self, workbook, data, records):
        format1 = workbook.add_format({'font_size': 12, 'border': True ,'align': 'center', 'bold': True})
        header_row = workbook.add_format({'font_size': 10, 'border': True, 'align': 'left', 'bold': True})
        rec_data = workbook.add_format({'font_size': 11, 'border': True, 'align': 'center'})
        sheet = workbook.add_worksheet('Category Report Detail')
        sheet.set_column(0, 35, 18)
        sheet.merge_range(0, 0, 2, 4, 'Sales & Purchase Summary', format1)
        row = 3
        col = 0
        sheet.write(row, col, 'Product SKU', header_row)
        sheet.write(row, col + 1, 'Product Name', header_row)
        sheet.write(row, col + 2, 'On Hand Qty', header_row)
        sheet.write(row, col + 3, 'Sales Qty', header_row)
        sheet.write(row, col + 4, 'Purchase Qty', header_row)
        rec_row = 4

        products_tmpl = self.env['product.template'].search([('sku_shatha', 'in', [False, 'None'])])
        for product_tmpl in products_tmpl:
            product_stock = self.env['stock.quant'].read_group(domain=[('product_tmpl_id', '=', product_tmpl.id), ('location_id.usage', '=', 'internal')],fields=['available_quantity'],groupby=['product_id', 'location_id'])
            product_stock_sale = self.env['stock.quant'].read_group(domain=[('product_tmpl_id', '=', product_tmpl.id), ('location_id.usage', '=', 'customer')],fields=['available_quantity'],groupby=['product_id'])
            if product_stock:
                sheet.write(rec_row, 0,'{0}'.format(str(product_tmpl.default_code)) if str(product_tmpl.default_code) != '' else '-',rec_data)
                sheet.write(rec_row, 1, '{0}'.format(product_tmpl.name) if product_tmpl.name != False else '-',rec_data)
                sheet.write(rec_row, 2, '{0}'.format(product_stock[0]['available_quantity']) if product_stock[0]['available_quantity'] != False else '0',rec_data)
                if product_stock_sale:
                    sheet.write(rec_row, 3, '{0}'.format(product_stock_sale[0]['available_quantity']) if product_stock_sale[0]['available_quantity'] != False else '0',rec_data)
                rec_row = rec_row + 1
