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

    # name = fields.Char('Location Name', required=True)
    #
    # location_name = fields.Char(required=True)  # For internal identification
    #
    # location_id = fields.Many2one('stock.location', 'Parent Location', index=True, ondelete='cascade', check_company=True, required=True,
    #     help="The parent location that includes this location. Example : The 'Dispatch Zone' is the 'Gate 1' parent location.")
    #
    # _sql_constraints = [
    #     ('name_location_id_unique', 'unique (location_id, name)',
    #      'The combination code/payment type already exists!'),
    # ]
    #
    #
    # _sql_constraints = [('name_location_name_unique', 'unique (name, location_id)', 'The combination code/payment type already exists!'),]
