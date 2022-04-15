from odoo import models, fields


class Product(models.Model):
    _inherit = 'product.product'

    item_type = fields.Selection([
        ('GS1', 'GS1'),
        ('EGS', 'EGS')
    ], string='Item type')
    item_code = fields.Char('Item code')
