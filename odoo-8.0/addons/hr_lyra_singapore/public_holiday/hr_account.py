import logging
from datetime import datetime
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

alpha_num_valid = re.compile(r"""(^[a-zA-Z0-9]{1,50}$)""", re.VERBOSE)

class hr_fiscalyear(osv.osv):
    _name = "hr.fiscalyear"
    _description = "HR Fiscal Year"
    _columns = {
        'name': fields.char('Fiscal Year', required=True),
        'code': fields.char('Code', size=6, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'period_ids': fields.one2many('hr.period', 'fiscalyear_id', 'Periods'),
        'state': fields.selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False),
        
    }
    _defaults = {
        'state': 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    _order = "date_start, id"

    def _check_duration(self, cr, uid, ids, context=None):
        obj_fy = self.browse(cr, uid, ids[0], context=context)
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]

    def create(self, cr, uid, values, context=None):
        id = super(hr_fiscalyear, self).create(cr, uid, values, context=context)
        return id 
    
    def write(self, cr, uid, ids, values, context=None):
        res = super(hr_fiscalyear, self).write(cr, uid, ids, values, context=context)
        return res   

    def validate_fields(self, cr, uid, values, context=None):
        if values and values.has_key('name') and values['name']:
            if not alpha_num_valid.match(values['name']):
                raise osv.except_osv(_('Validation Error'),_('Enter Valid Name!!.')) 
        if values and values.has_key('code') and values['code']:
            if not alpha_num_valid.match(values['code']):
                raise osv.except_osv(_('Validation Error'),_('Enter Valid Code!!.'))  
        return True

    def create_period3(self, cr, uid, ids, context=None):
        return self.create_period(cr, uid, ids, context, 3)

    def create_period(self, cr, uid, ids, context=None, interval=1):
        closing = False
        period_obj = self.pool.get('hr.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    closing = True
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                    'closing':closing,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def close_fy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done'}, context=context)

class hr_period(osv.osv):
    _name = "hr.period"
    _description = "HR period"
    _columns = {
        'name': fields.char('Period Name', required=True),
        'code': fields.char('Code', size=12),
        'closing': fields.boolean('Closing Period'),
        'date_start': fields.date('Start of Period', required=True),
        'date_stop': fields.date('End of Period', required=True),
        'fiscalyear_id': fields.many2one('hr.fiscalyear', 'Fiscal Year', required=True, select=True),
        'company_id': fields.related('fiscalyear_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True)
    }
    _defaults = {
    }
    _order = "date_start, closing desc"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]

    def _check_duration(self,cr,uid,ids,context=None):
        obj_period = self.browse(cr, uid, ids[0], context=context)
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self,cr,uid,ids,context=None):
        for obj_period in self.browse(cr, uid, ids, context=context):
            if obj_period.closing:
                continue

            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search(cr, uid, [('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop),('closing','=',False),('id','<>',obj_period.id)])
            for period in self.browse(cr, uid, pids):
                if period.fiscalyear_id.company_id.id==obj_period.fiscalyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
    ]
