
from odoo import fields, models,api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    lvl_1_categ_ids = fields.Many2many(
        comodel_name="product.category",
        relation="product_categ_rel",
        column1="product_id",
        column2="categ_id",
        string="Level 1",
        domain=[('categ_lvl', '=', 'lvl1')],
    )

    lvl_2_categ_ids = fields.Many2many(
        comodel_name="product.category",
        relation="product_categ_rel",
        column1="product_id",
        column2="categ_id",
        string="Level 2",
        domain=[('categ_lvl', '=', 'lvl2')],
    )

    lvl_3_categ_ids = fields.Many2many(
        comodel_name="product.category",
        relation="product_categ_rel",
        column1="product_id",
        column2="categ_id",
        string="Level 3",
        domain=[('categ_lvl', '=', 'lvl3')],
    )

    lvl_4_categ_ids = fields.Many2many(
        comodel_name="product.category",
        relation="product_categ_rel",
        column1="product_id",
        column2="categ_id",
        string="Level 4",
        domain=[('categ_lvl', '=', 'lvl4')],
    )

    @api.onchange('lvl_1_categ_ids','lvl_2_categ_ids','lvl_3_categ_ids','lvl_4_categ_ids')
    def _onchange_categ_levels(self):
        for rec in self:
            if rec.lvl_1_categ_ids or rec.lvl_2_categ_ids or rec.lvl_3_categ_ids:
                return {'domain': {
                                   'lvl_2_categ_ids': [('parent_id', 'in', rec.lvl_1_categ_ids.ids)],
                                    'lvl_3_categ_ids': [('parent_id', 'in', rec.lvl_2_categ_ids.ids)],
                                    'lvl_4_categ_ids': [('parent_id', 'in', rec.lvl_3_categ_ids.ids)],
                                   }}
            else:
                return {
                    'domain': {
                        'lvl_2_categ_ids': [],
                        'lvl_3_categ_ids': [],
                        'lvl_4_categ_ids': []
                    }
                }


class ProductCategory(models.Model):
    _inherit = "product.category"

    categ_lvl = fields.Selection([('lvl1', 'Level 1'), ('lvl2', 'Level 2'),('lvl3', 'Level 3'), ('lvl4', 'Level 4')], string="Category Level")

    def _compute_product_count(self):
        for categ in self:
            categ.product_count = self.env["product.template"].search_count(
                ["|",
                    ("lvl_1_categ_ids", "child_of", categ.id),
                    ("lvl_2_categ_ids", "child_of", categ.id),
                    ("lvl_3_categ_ids", "child_of", categ.id),
                    ("lvl_4_categ_ids", "child_of", categ.id),
                    ("categ_id", "child_of", categ.id),
                ]
            )
