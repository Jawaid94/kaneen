from odoo import fields, models
from odoo.exceptions import ValidationError
import base64
import csv
from io import StringIO, BytesIO


class ImportStockInvnetoryAdjustments(models.TransientModel):
    _name = "ywt.import.stock.inventory.adjustments"

    is_validate_inventory = fields.Boolean(string="Validate Inventory")

    select_file = fields.Binary(string='Select File')
    datas = fields.Binary(string='File Data')

    selectedfile_name = fields.Char(string='Filename', size=512)

    import_productby = fields.Selection(
        [('name', 'Name'), ('default_code', 'Internal Reference'), ('barcode', 'Barcode')], default='default_code',
        string="Import Product By")
    file_delimiter = fields.Selection([(',', 'Comma')], default=',', string="Delimiter",
                                      help="Select a delimiter to process CSV file.")

    stocklocation_id = fields.Many2one("stock.location", string="Source Location")

    def process_inventory_adjustments(self):
        select_inventory_file = self.validate_process()
        stock_quant_obj = self.env['stock.quant']
        product_product_obj = self.env['product.product']
        inventory_log_obj = self.env['ywt.import.stock.inventory.log']

        if select_inventory_file:

            file_name = self.selectedfile_name
            index = file_name.rfind('.')
            flag = 0
            if index == -1:
                flag = 1
            extension = file_name[index + 1:]

            if flag or extension not in ['csv']:
                raise ValidationError('Please Provide only .csv file')

            stock_location = self.stocklocation_id

            log_record = inventory_log_obj.log_record(operation_type="import")
            product_id = False

            self.write({'datas': self.select_file})
            self._cr.commit()

            imp_file = BytesIO(base64.b64decode(self.datas))
            csvf = StringIO(imp_file.read().decode())
            file_lines = csv.DictReader(csvf, delimiter=',')
            for file_line in file_lines:
                if self.import_productby == 'name':
                    if not file_line.get('Name', {}):
                        continue
                    product_name = file_line.get('Name').strip()
                    if product_name is not None:
                        product_id = product_product_obj.search([('name', '=', product_name)], limit=1)
                        if not product_id:
                            msg = "Product Not Found Product Name %s" % product_name
                            log_record.post_log_line(msg, type='mismatch')
                elif self.import_productby == 'default_code':
                    if not file_line.get('Default Code'):
                        continue
                    product_code = file_line.get('Default Code').strip()
                    if product_code is not None:
                        product_id = product_product_obj.search([('default_code', '=', product_code)], limit=1)
                        if not product_id:
                            msg = "Product Not Found Product Internal Reference %s" % product_code
                            log_record.post_log_line(msg, type='mismatch')
                elif self.import_productby == 'barcode':
                    if not file_line.get('Barcode', {}):
                        continue
                    product_barcode = file_line.get('Barcode').strip()
                    if product_barcode is not None:
                        product_id = product_product_obj.search([('barcode', '=', product_barcode)], limit=1)
                        if not product_id:
                            msg = "Product Not Found Product Barcode %s" % product_barcode
                            log_record.post_log_line(msg, type='mismatch')

                quantity = file_line.get('Quantity').strip()
                if not quantity:
                    raise ValidationError('Please Enter Quantity Column')
                if product_id and quantity:
                    stock_quant_obj = stock_quant_obj.search(
                        [
                            ('product_id', '=', product_id.id),
                            ('location_id', '=', stock_location.id)
                        ], limit=1)
                    if stock_quant_obj:
                        stock_quant_obj.update({'inventory_quantity': quantity})
                    else:
                        stock_inventory_line_vals = self.prepare_invnetory_adjustments_line_vals(product_id,
                                                                                                 quantity,
                                                                                                 stock_location)
                        stock_quant_obj = stock_quant_obj.create(stock_inventory_line_vals)

                    if self.is_validate_inventory:
                        stock_quant_obj.action_apply_inventory()

            if not log_record.log_line_ids:
                log_record.sudo().unlink()

    def validate_process(self):
        if not self.select_file:
            raise ValidationError('Please Select File to Process...')
        return True

    def prepare_invnetory_adjustments_line_vals(self, product_id, quantity, stock_location):
        vals = {
            'location_id': stock_location and stock_location.id,
            'company_id': stock_location and stock_location.company_id.id,
            'product_id': product_id and product_id.id,
            'product_uom_id': product_id and product_id.uom_id.id,
            'inventory_quantity': quantity
        }
        return vals