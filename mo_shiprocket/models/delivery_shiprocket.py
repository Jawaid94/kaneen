import requests
import json
from odoo.exceptions import ValidationError
from odoo import api, models, fields, _

base_url = "https://api.shiprocket.ae/"

auth_code_url = "{url}/api/v1/oauth/authorize?client_id={client_id}&response_type=code"
access_token_url = "{url}/api/v1/oauth/generate-token"

create_order_url = "{url}/api/v1/external/orders/create/adhoc"


class ShiprocketProvider(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[
        ('shiprocket', "Shiprocket")
    ], ondelete={'shiprocket': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    shiprocket_client_id = fields.Char('Client ID')

    def process_response(self, response):
        if response.status_code != 200:
            if response.status_code == 401:
                # reauth
                self.shiprocket_auth()
            else:
                raise ValidationError(_('Invalid Shiprocket Response: {}').format(response.text))

        return json.dumps(response)

    def shiprocket_auth(self):
        url = auth_code_url.format(base_url, self.shiprocket_client_id)

        response = requests.get(url)
