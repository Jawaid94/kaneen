from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    # serveasy_user = fields.Char("Test")
    user_role = fields.Many2one('user.roles', string='User Access', tracking=True)
    def _get_is_admin(self):
        """
        The Hide specific menu tab will be hidden for the Admin user form.
        Else once the menu is hidden, it will be difficult to re-enable it.
        """
        for rec in self:
            rec.is_admin = False
            if rec.id == self.env.ref('base.user_admin').id:
                rec.is_admin = True



    hide_menu_access_ids = fields.Many2many('ir.ui.menu', 'ir_ui_hide_menu_rel', 'uid', 'menu_id',
                                            string='Hide Access Menu')

    is_admin = fields.Boolean(compute=_get_is_admin)

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        self.self.clear_caches()
        return res


    @api.onchange('user_role')
    def _onchange_user_role_domain(self):
        ids = (self.user_role.hide_menu_ids).ids
        self.hide_menu_access_ids = ids

class RestrictMenu(models.Model):
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many('res.users')