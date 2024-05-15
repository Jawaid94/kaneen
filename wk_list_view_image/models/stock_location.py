from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.constrains('location_id', 'name')
    def _check_ref(self):
        for record in self:
            location = self.env['stock.location'].search(
                [('name', '=', record.name), ('location_id', '=', self.location_id.id)])
            if len(location) > 1:
                raise ValidationError(_("You can't create 2 Locations with the same Name and Parent Location"))

