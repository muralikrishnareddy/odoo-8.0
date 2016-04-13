# -*- coding: utf-8 -*-
# © 2016 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Public Holidays",
    'images': [],
    'summary': """Manage public holidays""",
    'author': "ONESTEiN BV",
    'license': 'AGPL-3',
    'website': "http://www.onestein.eu",
    'category': 'Human Resources',
    'version': '8.0.1.0.0',
    'depends': [
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
        #'data/hr_public_holiday.xml',
        'views/hr_public_holiday.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
