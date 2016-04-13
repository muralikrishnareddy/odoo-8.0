# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'HR for Lyra Singapore',
    'category': 'Human Resources', 
    'version': '1.0',
    'description': """
Human Resources Management.
====================

Customizations on Leave and Payroll.

    """,
    'author': 'Credativ Software (I) Pvt. Ltd.',
    'website': 'http://www.credativ.in',
    'sequence':1,
    'depends': ['base','hr','hr_contract','hr_holidays','hr_payroll','document'],
    'data': [          
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'hr_report.xml',
        'views/report_payslip.xml',
        'hr_payslip_view.xml',
        'working_schedule.xml',
        'public_holiday/hr_holiday_demo.xml',
        'public_holiday/hr_account_view.xml',
        'public_holiday/hr_holiday_view.xml',
        'public_holiday/public_holiday_view.xml',
        'half_day_leave/holiday_view.xml',
        'unpaid_salary_rule.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
