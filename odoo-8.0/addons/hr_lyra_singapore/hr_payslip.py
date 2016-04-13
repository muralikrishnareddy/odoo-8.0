# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import os
import re
import openerp
from openerp import SUPERUSER_ID, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools import image_resize_image
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.amount_to_text_en import amount_to_text
import locale

from openerp.tools.safe_eval import safe_eval as eval
  
  
class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _columns ={
        'emp_number':fields.char('Employee Number'),
        'appointed_on':fields.date('Appointed On'),
        'emp_cpf_number':fields.char('Employee CPF No.'),
    }
    
class hr_contract(osv.osv):
    _inherit = "hr.contract"
    _columns ={
        'employee_cpf':fields.float('Employee CPF Amount', digits_compute=dp.get_precision('Payroll')),
        'employee_cpf_per':fields.float('Employee CPF %'),
        'employer_cpf':fields.float('Employer CPF Amount', digits_compute=dp.get_precision('Payroll')),
        'employer_cpf_per':fields.float('Employer CPF %'),
        'emp_number':fields.related('employee_id', 'emp_number', type='char', relation='hr.employee', string='Employee Number'),
    }  
    
    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        ret = super(hr_contract,self).onchange_employee_id(cr, uid, ids, employee_id,context=context)
        if employee_id:
            emp = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            ret['value']['emp_number'] = emp.emp_number
        else:
            ret['value']['emp_number'] = False
        return ret
    
                
class hr_salary_rule(osv.osv):
    _inherit = "hr.salary.rule"
    _columns ={
        'flg_print':fields.boolean('Print Values'),
    }  
    _defaults = {
        'flg_print':False,
    }
    
    
class hr_payslip(osv.osv):
    _inherit = "hr.payslip"
    count=15
    
    _columns = {
        'emp_number':fields.related('employee_id', 'emp_number', type='char', relation='hr.employee', string='Employee Number'),
    }
    
    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        ret = super(hr_payslip,self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        if employee_id:
            emp = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            ret['value']['emp_number'] = emp.emp_number
        else:
            ret['value']['emp_number'] = False
        return ret
    
    def get_company_address(self,company):
        #company = self.browse(self.cr, uid, company_id)
        address = ''
        address+=company.street and company.street+' ' or ''
        address+=company.street2 and company.street2+' ' or ''
        address+=company.city and company.city+' ' or ''
        address+=company.state_id and company.state_id.name+' ' or ''
        address+=company.country_id and company.country_id.name+' ' or ''
        address+=company.zip and company.zip or ''
        return address
        
    def get_company_phone(self,company):
        address = ''
        address+=company.phone and 'Tel: '+company.phone+' ' or ''
        address+=company.fax and 'Fax: '+company.fax+' ' or ''
        address+=company.website and company.website.replace('http://','') or ''
        return address
        
    def get_salary_month(self, date_from):
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        return tools.ustr(ttyme.strftime('%B - %Y'))
    
    def get_location(self, obj):
        return obj.employee_id.work_location and obj.employee_id.work_location or obj.company_id.country_id.name
        
    def get_worked_days(self,obj):
        total=0
        for line in obj.worked_days_line_ids:
            if line.code == 'WORK100':
                total+=line.number_of_days
        return total
        
    def get_earnings(self,line_ids):    
        objs=[]
        ded=[]
        total=0.00
        for line in line_ids:
            if line.category_id.code.upper()=='BASIC':
                objs.append(line)
                total+=line.total
            elif line.category_id.code.upper()=='ALW':
                objs.append(line)
                total+=line.total    
            elif line.category_id.code.upper()=='DED':
                ded.append(line)
        count = max(len(objs),len(ded),self.count)
        for _ in range(count-len(objs)): 
            MyObject = type('hr.payslip.line', (object,), {})
	    obj = MyObject()
	    obj.name=' '
	    obj.total=False
            objs.append(obj)
        return objs        
        
    def get_deductions(self,line_ids):    
        objs=[]
        ear=[]
        total=0.00
        for line in line_ids:
            if line.category_id.code.upper()=='DED':
                objs.append(line)
                total+=line.total
            elif line.category_id.code.upper()=='BASIC':
                ear.append(line)
            elif line.category_id.code.upper()=='ALW':
                ear.append(line)
        count = max(len(objs),len(ear),self.count)
        for _ in range(count-len(objs)): 
            MyObject = type('hr.payslip.line', (object,), {})
	    obj = MyObject()
	    obj.name=' '
	    obj.total=False
            objs.append(obj)
        return objs  
        
    def get_gross_pay_total(self, obj):
        total=0.00
        for line in obj.line_ids:
            if line.category_id.code.upper()=='BASIC':
                total+=line.total
            elif line.category_id.code.upper()=='ALW':
                total+=line.total    
        return total
        
    def get_gross_deductions_total(self, obj):
        total=0.00
        for line in obj.line_ids:
            if line.category_id.code.upper()=='DED':
                total+=line.total
        return total
        
    def get_net_total(self, obj):
        ptotal=0.00
        locale.setlocale(locale.LC_ALL, 'en_IN')
        for line in obj.line_ids:
            if line.category_id.code.upper()=='NET':  
                ptotal = line.total
        #decimals = str(ptotal).split('.')[1]
        #ptotal = locale.format("%d", ptotal, grouping=True)
        #ptotal = float(ptotal)
        #ptotal+=float('0.'+str(decimals))
        return ptotal 
        
    def get_net_total_words(self, obj):
        ptotal=0.00
        for line in obj.line_ids:
            if line.category_id.code.upper()=='NET':  
                ptotal = line.total
              
        return amount_to_text(ptotal, currency=obj.company_id.currency_id.name)
        
    def _amount_to_text(self, cr, uid, amount, currency_id, context=None):
        # Currency complete name is not available in res.currency model
        # Exceptions done here (EUR, USD, BRL) cover 75% of cases
        # For other currencies, display the currency code
        currency = self.pool['res.currency'].browse(cr, uid, currency_id, context=context)
        if currency.name.upper() == 'EUR':
            currency_name = 'Euro'
        elif currency.name.upper() == 'USD':
            currency_name = 'Dollars'
        elif currency.name.upper() == 'BRL':
            currency_name = 'reais'
        else:
            currency_name = currency.name
        #TODO : generic amount_to_text is not ready yet, otherwise language (and country) and currency can be passed
        #amount_in_word = amount_to_text(amount, context=context)
        return amount_to_text(amount, currency=currency_name)
        
    def get_name_for_report(self,line):
        ret = line.name
        if line.name.strip()!='' and line.salary_rule_id and line.salary_rule_id.flg_print:
            if line.salary_rule_id.code.upper() == 'CPF':#Employee CPF in Deductions
                ret = line.name + ' (%s' % (line.slip_id.contract_id and line.slip_id.contract_id.employee_cpf_per or '') +'%' + ' of %.2f)'%(line.slip_id.contract_id and round(line.slip_id.contract_id.employee_cpf,2) or '')
            if line.salary_rule_id.code.upper() in ('ECPF','ECPFD'):#Employer CPF in Allowance
                ret = line.name + ' (%s' % (line.slip_id.contract_id and line.slip_id.contract_id.employer_cpf_per or '') +'%' + ' of %.2f)'%(line.slip_id.contract_id and round(line.slip_id.contract_id.employer_cpf,2) or '')
            if line.salary_rule_id.code.upper() == 'OT':#Over Time
                ret = line.name + ' (%s * %.2f)' % (line.quantity,line.amount)    
        return ret
        


                            
        
        
