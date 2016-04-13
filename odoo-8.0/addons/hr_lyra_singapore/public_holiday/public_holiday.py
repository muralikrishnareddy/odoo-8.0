import logging
from datetime import datetime, date, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import re
import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools.safe_eval import safe_eval as eval

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class public_holiday(osv.osv):
    _name = "public.holiday"
    _description = "Public Holiday"
    _rec_name = 'fiscalyear_id'
    
    def get_holiday(self, cr, uid, context=None):
        holiday = self.pool.get('hr.holidays.status').search(cr, uid, [('holiday','=',True)],context=context)
        if holiday:
            return holiday[0]
        else:
            return False        
        return True
    
    
    _columns = {
        'fiscalyear_id': fields.many2one('hr.fiscalyear', 'Fiscal Year', required=True, select=True),
        'holiday_ids': fields.one2many('public.holiday.lines', 'holiday_id', 'Holidays'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'holiday_status_id':fields.many2one('hr.holidays.status', 'Related Public Holidays Leave'),
        'state':fields.selection([('new','New'),('created','Configured')], string='Status'),
    }
    
    _defaults = {
        'state':'new',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'holiday_status_id': get_holiday,
        
    }
    
    _order = "id"
    _sql_constraints = [
        ('holiday_uniq', 'unique(fiscalyear_id,company_id)', 'Holidays are already created for this Year for this company!'),
    ]

    def create_holidays(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if context.has_key('active_employee_id'):
                emp_ids = context['active_employee_id']
            else:
                emp_ids = self.pool.get('hr.employee').search(cr, uid, [])
            leave_ids = []
            holiday_dates = []
            if not emp_ids:
                continue
                raise osv.except_osv(_('ERROR !!'), _('Employees Not Found. Please check with Administrator'))
            for line in record.holiday_ids:
                holiday_dates.append(line.date)
                for emp in self.pool.get('hr.employee').browse(cr, uid, emp_ids, context=context):
                    _logger.info("Configuring Leaves for %s", emp.name)
                    vals = {
                                'name': 'Official Holiday - %s'%line.holiday_name,
                                'type': 'remove',
                                'holiday_type': 'employee',
                                'holiday_status_id': record.holiday_status_id.id,
                                'date_from': line.date + ' 03:30:00',
                                'date_to': str(datetime.strptime(line.date + ' 03:30:00', tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=8)),
                                'number_of_days_temp': 1,
                                'employee_id': emp.id
                            }
                    leave_id = self.pool.get('hr.holidays').create(cr, uid, vals, context=context)
                    leave_ids.append(leave_id)
                    print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$", leave_id
            for leave_id in leave_ids:
                    # TODO is it necessary to interleave the calls?
                for sig in ('confirm', 'validate', 'second_validate'):
                    self.pool.get('hr.holidays').signal_workflow(cr, uid, [leave_id], sig)
            if context.has_key('active_employee_id'):
                return True
        self.write(cr, uid, ids, {'state':'created'}, context=context)
        return True    
    
public_holiday()

class public_holiday_lines(osv.osv):
    _name = "public.holiday.lines"
    _description = "Public Holidays"
    _rec_name = 'holiday_name'
    
    def _get_fiscal_year(self, cr, uid, ids, name, args, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.holiday_id:
                result[line.id] = line.holiday_id.fiscalyear_id.id
            else:
                result[line.id] = line.opt_holiday_id.fiscalyear_id.id
        return result
    
    _columns = {
        'holiday_id': fields.many2one('public.holiday', 'Holiday'),
        'opt_holiday_id': fields.many2one('public.holiday', 'Holiday'),
        'holiday_name': fields.char('Holiday Name', size=120, required=True),
        'date': fields.date('Date', required=True),
        'company_id': fields.related('holiday_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'fiscalyear_id': fields.function(_get_fiscal_year, type='many2one', relation='hr.fiscalyear', string='Fiscal Year', store=True)
    }
    _sql_constraints = [
        ('holiday_date_uniq', 'unique(date)', 'Holiday Date must be Unique !!'),
    ]
    _order = "date"
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.holiday_name +':'+record.date
            res.append((record.id, name))
        return res
    
public_holiday_lines() 