# -*- coding: utf-8 -*-
{
    'name': 'Egypt E-Invoice',
    'category': 'Tools',
    'summary': 'Check printing commons',
    'description': "",
    'depends': ['base', 'account', 'stock'],
    'data': [
        'views/account_move_inherit.xml',
        'views/res_company_res_partner_inherit.xml',
        'views/uom_inherit.xml',
        'views/product_product_inherit.xml',
        'views/account_tax_inherit.xml',
        'views/state_cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
