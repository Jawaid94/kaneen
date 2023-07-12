# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition


class Report(http.Controller):

    @http.route('/report/invoice/<int:magento_order_id>', type='http', auth="public")
    def invoice(self, magento_order_id, **kwargs):
        invoice_type = kwargs.get('type', 'out_invoice')

        headers = []

        error = False
        error_wrapper = """<html>
                       <head>
                       <title>Error</title>
                       </head>
                       <body>
                           <p>Can not get invoice.</br> %s </p>
                       </body>
                       </html>"""
        error_text = ""

        token = request.env['ir.config_parameter'].sudo().get_param('mo_magento.report_token')

        # if not kwargs.get("token", False) or (kwargs.get("token", False) and kwargs['token'] != token):
        #     error_text += "Invalid token.<br/>"
        #     error_wrapper %= error_text
        #     headers.append(('Content-Length', len(error_wrapper)))
        #     response = request.make_response(error_wrapper, headers)
        #     response.mimetype = 'text/html'
        #
        #     return response
        #
        # if invoice_type not in ['out_invoice', 'out_refund']:
        #     error_text += "Invalid invoice type.<br/>"
        #     error = True

        sale_order = request.env['sale.order'].sudo().search([('magento_order_id', '=', magento_order_id)])

        if not sale_order:
            error_text += "Can not find order by {}.<br/>".format(magento_order_id)
            error = True

        sale_invoices = sale_order.invoice_ids.filtered(lambda x: x.state not in ['cancel', 'draft'])

        if not sale_invoices:
            error_text += "Can not find any invoice in order {}.<br/>".format(sale_order.name)
            error = True

        need_invoice = sale_invoices.filtered(lambda x: x.move_type == invoice_type)

        if not need_invoice and sale_invoices:
            error_text += "Can not find any invoice in order {} with type {}.<br/>".format(sale_order.name, invoice_type)
            error = True

        if error:
            error_wrapper %= error_text
            headers.append(('Content-Length', len(error_wrapper)))
            response = request.make_response(error_wrapper, headers)
            response.mimetype = 'text/html'

            return response

        tmpl = request.env.ref('mo_kaneen.lbs_report_invoice_custom_document_action')
        pdf = tmpl.sudo()._render_qweb_pdf(need_invoice.ids)[0]

        names = need_invoice.mapped('name')
        names = map(lambda s: s.replace("/", ""), names)

        filename = 'Invoice - %s' % (','.join(names))

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf))
        ]

        if "download" in kwargs and kwargs['download']:
            headers.append((
                'Content-Disposition',
                content_disposition(filename + '.pdf')
            ))
        else:
            headers.append((
                'Content-Disposition', 'filename=%s.pdf' % filename
            ))

        response = request.make_response(pdf, headers)
        response.mimetype = 'application/pdf'

        return response

