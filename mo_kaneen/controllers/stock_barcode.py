from collections import defaultdict

from odoo import http, _
from odoo.http import request
from odoo.osv import expression
from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController


class StockBarcodeControllerKaneen(StockBarcodeController):

    def _get_barcode_field_by_model(self):
        result = super()._get_barcode_field_by_model()
        result.update({
            'product.barcode.multi': 'name'
        })
        return result

    @http.route('/stock_barcode/get_specific_barcode_data', type='json', auth='user')
    def get_specific_barcode_data(self, barcode, model_name, domains_by_model=False):
        nomenclature = request.env.company.nomenclature_id
        # Adapts the search parameters for GS1 specifications.
        operator = '='
        limit = None if nomenclature.is_gs1_nomenclature else 1
        if nomenclature.is_gs1_nomenclature:
            try:
                # If barcode is digits only, cut off the padding to keep the original barcode only.
                barcode = str(int(barcode))
                operator = 'ilike'
            except ValueError:
                pass  # Barcode isn't digits only.

        domains_by_model = domains_by_model or {}
        barcode_field_by_model = self._get_barcode_field_by_model()
        result = defaultdict(list)
        model_names = model_name and [model_name] or list(barcode_field_by_model.keys())
        for model in model_names:
            domain = [(barcode_field_by_model[model], operator, barcode)]
            domain_for_this_model = domains_by_model.get(model)
            if domain_for_this_model:
                domain = expression.AND([domain, domain_for_this_model])
            record = request.env[model].with_context(display_default_code=False).search(domain, limit=limit)
            if record:
                if record._name == 'product.barcode.multi':
                    record = record.product_id
                    model = 'product.product'

                result_search = record.read(request.env[model]._get_fields_stock_barcode(), load=False)
                if model == 'product.product':
                    result_products = []
                    for product in result_search:
                        barcodes = request.env['product.barcode.multi'].browse(product['barcode_ids'])
                        product.update({
                            'barcodes': barcodes.mapped("name")
                        })
                        result_products.append(product)

                    result[model] = result_products
                else:
                    result[model] = result_search

                if hasattr(record, '_get_stock_barcode_specific_data'):
                    additional_result = record._get_stock_barcode_specific_data()
                    for key in additional_result:
                        result[key] += additional_result[key]
        return result
