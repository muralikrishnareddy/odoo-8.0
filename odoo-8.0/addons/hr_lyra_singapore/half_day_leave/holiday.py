from openerp.osv import osv, fields
import time
import datetime
from dateutil.relativedelta import relativedelta
import math
import logging
from openerp.tools.translate import _
from openerp import tools
from dateutil.relativedelta import *
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class hr_holidays(osv.osv):
    
    _inherit = 'hr.holidays'
    _order = 'id desc'
    _columns = {
                'half_day':fields.boolean('Half Day'),
                'temp_days_readonly':fields.float('Temp Days'),
                }
    _defaults={
               'half_day':False,
               }

    def create(self, cr, uid, vals, context=None):
        if vals and vals.has_key('type') and vals['type'] == 'remove' and vals.has_key('temp_days_readonly'):
            vals['number_of_days_temp'] = vals['temp_days_readonly']
        return super(hr_holidays, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        print "---UPdate Employee Leave----", vals
        if vals and vals.has_key('temp_days_readonly'):
            vals['number_of_days_temp'] = vals['temp_days_readonly']
        super(hr_holidays, self).write(cr, uid, ids, vals, context=context)
        return True

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day

    def onchange_date_from(self, cr, uid, ids, date_to, date_from, employee_id, half_day):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}
        warnings = ''
        if date_from:
            date_from = date_from.split(' ')[0] + ' 01:30:00'
            result['value']['date_from'] = date_from

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)
        if date_from and half_day:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
            result['value']['date_to'] = str(date_to_with_delta)
            
        if (date_to and date_from) and (date_from <= date_to):
            if half_day:
                result['value']['number_of_days_temp'] = 0.5
                result['value']['temp_days_readonly'] = 0.5
            else:      
                diff_day = self._get_number_of_days(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
        else:
            result['value']['number_of_days_temp'] = 0
            result['value']['temp_days_readonly'] = 0                
        return result
    
    def onchange_date_to(self, cr, uid, ids, date_to, date_from, employee_id, half_day):
        """
        Update the number_of_days.
        """

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}
        warnings = ''
        if date_from:
            date_from = date_from.split(' ')[0] + ' 01:30:00'
            result['value']['date_from'] = date_from

        result = {'value': {}}
            
        if (date_to and date_from) and (date_from <= date_to):
            if half_day:
                result['value']['number_of_days_temp'] = 0.5
                result['value']['temp_days_readonly'] = 0.5
            else:      
                diff_day = self._get_number_of_days(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
        else:
            result['value']['number_of_days_temp'] = 0
            result['value']['temp_days_readonly'] = 0                
        return result        

    def on_change_half_day(self, cr, uid, ids, half_day, date_from, date_to):
        value = {}
        if date_from and (not half_day):
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            date_to = date_to or str(date_to_with_delta)
            return {'value':{'date_from':date_from, 'date_to':date_to}}
        date_to = ''
        if date_from:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
            date_to = str(date_to_with_delta)
            value = {'date_from':date_from, 'date_to':date_to, 'number_of_days_temp':0.5, 'temp_days_readonly':0.5}
        return {'value':value}
    
hr_holidays()   