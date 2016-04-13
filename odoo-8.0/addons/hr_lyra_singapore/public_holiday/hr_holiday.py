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
import datetime as dt

_logger = logging.getLogger(__name__)

class hr_holidays_status(osv.osv):
    
    _inherit = 'hr.holidays.status'

    _columns = {
                'holiday':fields.boolean('Office Holiday', help="Check if this leave is used only for office purpose, for ex: public holidays, saturday off etc"),
                'code':fields.char('Code', size=10),
                'max_days':fields.float('Maximum Days / Allocation', help="Allocation Limit."),
                'need_certificate':fields.boolean('Need Certificate', help="Check if this leave needs Certificate/Proofs."),
                'eligible_months':fields.integer('Eligible After (in months)', help='Months after this leave is Applicable.'),
                }

    _defaults={
               }
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'This Code is already Exists !!'),
    ]
    
hr_holidays_status()                 

class hr_holidays(osv.osv):
    
    _inherit = 'hr.holidays'
    _order = 'id desc'
    _columns = {
                'holiday':fields.related('holiday_status_id', 'holiday', type='boolean', string='Holiday',store=True),
                'fiscalyear_id':fields.many2one('hr.fiscalyear','Fiscal Year'), 
                'certificate':fields.binary('Certificate', help="Attach the proof against the leave request"),
                'need_certificate':fields.related('holiday_status_id', 'need_certificate', type='boolean', string='Need Certificate', store=True),
                
                }

    def _get_fiscalyear(self, cr, uid, context=None):
        today = time.strftime("%Y-%m-%d")
        fiscalyear = self.pool.get('hr.fiscalyear').search(cr, uid, [('date_start','<=',today),('date_stop','>=',today),('state','=','draft')])
        return fiscalyear and fiscalyear[0] or False
    
    _defaults = {
                 'fiscalyear_id':_get_fiscalyear,
                 }

    def onchange_holiday_status_id(self, cr, uid, ids, holiday_status_id):
        result = {'value': {'holiday': False,'need_certificate':False}}
        if holiday_status_id:
            status = self.pool.get('hr.holidays.status').browse(cr, uid, holiday_status_id)
            result['value'] = {'holiday': status.holiday,'need_certificate':status.need_certificate}
        return result

    def months_between(self,date1,date2):
        if date1>date2:
            date1,date2=date2,date1
        m1=date1.year*12+date1.month
        m2=date2.year*12+date2.month
        months=m2-m1
        if date1.day>date2.day:
            months-=1
        elif date1.day==date2.day:
            seconds1=date1.hour*3600+date1.minute+date1.second
            seconds2=date2.hour*3600+date2.minute+date2.second
            if seconds1>seconds2:
                months-=1
        return months

    def validate_request(self, cr, uid, ids, context=None):
        context = context and dict(context) or {}
        for leave in self.browse(cr, uid, ids, context=context):
            status = leave.holiday_status_id
            employee = leave.employee_id
            if not status.holiday:
                if not employee.appointed_on:
                    raise osv.except_osv(_('Configuration Error!'), _('Appointment Date not found for Employee - %s.')%(employee.name))
                if leave.type == 'add':
                    if leave.number_of_days_temp > status.max_days:
                        raise osv.except_osv(_('Not Allowed!'), _('Maximum Allocation for this Leave Type is %s days.')%(status.max_days))
                else:
                    if status.need_certificate and (not leave.certificate):
                        raise osv.except_osv(_('Not Attached!!'),_('Please attach medical certificate.'))
                    if not context.has_key('no_check'):
                        emp_joining = datetime.strptime(employee.appointed_on, '%Y-%m-%d')
                        today = datetime.today()
                        months = self.months_between(today, emp_joining)
                        if months < status.eligible_months:
                            raise osv.except_osv(_('Not Eligible!!'),_('You are not yet eligible for this leave type.'))
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        context = context and dict(context) or {}
        super(hr_holidays, self).write(cr, uid, ids, vals, context=context)
        context.update({'no_check':True})
        self.validate_request(cr, uid, ids, context=context)
        return True

    def create(self, cr, uid, values, context=None):
        """ Override to avoid automatic logging of creation """
        if context is None:
            context = {}
        context = dict(context, mail_create_nolog=True)
        if values.get('state') and values['state'] not in ['draft', 'confirm', 'cancel'] and not self.pool['res.users'].has_group(cr, uid, 'base.group_hr_user'):
            raise osv.except_osv(_('Warning!'), _('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
        leave = super(hr_holidays, self).create(cr, uid, values, context=context)
        self.validate_request(cr, uid, [leave], context=context)
        return leave
        
hr_holidays()              