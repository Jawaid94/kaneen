from odoo import models, fields, api, _
from .sale_order import quality_items


class ProductQuality(models.Model):
    _name = 'mo.product.quality.comment'
    _description = "Product Quality Comment"

    name = fields.Char("Comment", required=True)
    external_id = fields.Integer("External ID")
