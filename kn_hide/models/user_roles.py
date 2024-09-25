from odoo import fields, models, api

class UserRoles(models.Model):
    _name = 'user.roles'
    _description = 'User Roles'
    _rec_name = 'name'

    name = fields.Char(string="User Access Name", help="Use to define role againts the current user", required=True)
    hide_menu_ids = fields.Many2many('ir.ui.menu', string="Hide Menu", store=True,
                                     help='Select menu items that needs to be '
                                          'hidden to this user ')
    def write(self, vals):
        user_ids = self.env['res.users'].search([('user_role', '=', self.id)])
        for rec in user_ids:
            ids = rec.hide_menu_access_ids.ids
            for id in vals['hide_menu_ids']:
                ids.append(id[1])
            rec.hide_menu_access_ids = ids
        result = super(UserRoles, self).write(vals)
        return result

    def reset_menu_from_users(self):
        users = self.env['res.users'].search([])
        return True
        # for user in users:
        # for menu in self.hide_menu_ids:
        #     for user_id in self.ids:
        #         if user_id != self.env.user.id:
        #             menu.write({
        #                 'restrict_user_ids': [(4, user_id)]
        #             })

